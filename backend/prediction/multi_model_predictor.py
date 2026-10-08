# backend/prediction/multi_model_predictor.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 导入模型
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge

import xgboost as xgb
XGB_AVAILABLE = True

import joblib
import os
import re
from datetime import datetime

class MultiModelHousePricePredictor:
    """多模型房价预测器（样本量自适应 + 五模型对比 + 指标可视化）"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = None
        self.label_encoders = {}
        self.models = {}
        self.results = {}
        self.feature_names = []
        self.numeric_features = ['unit_price', 'area']
        self.categorical_features = ['district', 'orientation', 'decorate',
                                     'building_type', 'rooms', 'halls', 'floor_level']
        self.tag_features = ['has_vr', 'has_metro', 'has_elevator',
                            '满两年', '满五年', '唯一住房']

        # 按区县存储的模型
        self.district_models = {}
        self.district_scalers = {}
        self.district_avg_prices = {}
        self.district_data_stats = {}

        # 全局简单模型
        self.global_simple_model = None
        self.global_scaler = None

        # 存储每个区县所有候选模型的性能
        self.all_models_performance = {}

        self.load_data()

    def load_data(self):
        """加载CSV数据"""
        print(f"\n{'='*60}")
        print("1. 加载数据")
        print(f"{'='*60}")
        self.df = pd.read_csv(self.csv_path)
        print(f"数据形状: {self.df.shape}")
        print(f"数据列: {self.df.columns.tolist()}")
        print(f"\n数据预览:")
        print(self.df.head(3))

    def prepare_features(self):
        """准备特征工程（适配中文列名，清洗数值，解析户型）"""
        print(f"\n{'='*60}")
        print("2. 特征工程")
        print(f"{'='*60}")

        features = self.df.copy()

        # ---------- 列名映射（中文 → 英文）----------
        col_rename = {
            '楼层': 'floor',
            '区域': 'district',
            '朝向': 'orientation',
            '装修': 'decorate',
            '建筑类型': 'building_type',
            '面积(平米)': 'area',
            '均价(元/平)': 'unit_price',
            '价格(万)': 'total_price',
            '标签': 'tags'
        }
        for k, v in col_rename.items():
            if k in features.columns:
                features.rename(columns={k: v}, inplace=True)

        # 数据清洗：确保 total_price, unit_price, area 为数值
        for col in ['total_price', 'unit_price', 'area']:
            if col in features.columns:
                features[col] = features[col].astype(str).str.extract(r'(\d+(?:\.\d+)?)')[0]
                features[col] = pd.to_numeric(features[col], errors='coerce')

        # 删除 total_price 无效的行
        if 'total_price' in features.columns:
            invalid_price = features['total_price'].isna() | (features['total_price'] == 0)
            if invalid_price.any():
                print(f"警告: {invalid_price.sum()} 行的 total_price 无效，将被删除")
                features = features[~invalid_price].copy()

        # 填充缺失的面积和单价
        for col in ['area', 'unit_price']:
            if col in features.columns and features[col].isna().any():
                median_val = features[col].median()
                features[col].fillna(median_val, inplace=True)
                if col == 'area':
                    features[col] = features[col].clip(lower=0.1)

        # 解析户型得到 rooms 和 halls
        if '户型' in features.columns:
            def parse_rooms_halls(huxing):
                if pd.isna(huxing):
                    return 0, 0
                huxing_str = str(huxing)
                rooms_match = re.search(r'(\d+)室', huxing_str)
                halls_match = re.search(r'(\d+)厅', huxing_str)
                rooms = int(rooms_match.group(1)) if rooms_match else 0
                halls = int(halls_match.group(1)) if halls_match else 0
                return rooms, halls
            features[['rooms', 'halls']] = features['户型'].apply(
                lambda x: pd.Series(parse_rooms_halls(x))
            )
        else:
            if 'rooms' not in features.columns:
                features['rooms'] = 0
            if 'halls' not in features.columns:
                features['halls'] = 0

        # 从楼层信息中提取楼层级别
        def extract_floor_level(floor_str):
            if pd.isna(floor_str):
                return '中'
            floor_str = str(floor_str)
            if '低' in floor_str:
                return '低'
            elif '中' in floor_str:
                return '中'
            elif '高' in floor_str:
                return '高'
            else:
                return '中'

        if 'floor' in features.columns:
            features['floor_level'] = features['floor'].apply(extract_floor_level)
        else:
            features['floor_level'] = '中'

        # 从标签中提取特征
        def extract_tags(tags_str):
            if pd.isna(tags_str):
                return {
                    'has_vr': 0,
                    'has_metro': 0,
                    'has_elevator': 0,
                    '满两年': 0,
                    '满五年': 0,
                    '唯一住房': 0
                }
            tags_str = str(tags_str)
            return {
                'has_vr': 1 if 'VR' in tags_str else 0,
                'has_metro': 1 if '地铁' in tags_str or '近地铁' in tags_str else 0,
                'has_elevator': 1 if '电梯' in tags_str else 0,
                '满两年': 1 if '满两年' in tags_str else 0,
                '满五年': 1 if '满五年' in tags_str else 0,
                '唯一住房': 1 if '唯一' in tags_str else 0
            }

        if 'tags' in features.columns:
            tag_features = features['tags'].apply(extract_tags)
            tag_df = pd.DataFrame(tag_features.tolist())
            features = pd.concat([features, tag_df], axis=1)
        else:
            for tag in self.tag_features:
                features[tag] = 0

        # 编码分类变量（除了district）
        categorical_features = [col for col in self.categorical_features if col != 'district']
        for col in categorical_features:
            if col in features.columns:
                le = LabelEncoder()
                features[col + '_encoded'] = le.fit_transform(features[col].astype(str))
                self.label_encoders[col] = le
                print(f"编码 {col}: {len(le.classes_)} 个类别")
            else:
                print(f"警告: 分类列 {col} 不存在，将跳过")

        # 选择最终特征
        self.feature_names = (self.numeric_features +
                             [col + '_encoded' for col in categorical_features if (col + '_encoded') in features.columns] +
                             self.tag_features)
        self.feature_names = [f for f in self.feature_names if f in features.columns]

        # 准备特征矩阵和目标变量
        self.X = features[self.feature_names].copy()
        self.y = features['total_price'].copy()
        self.districts = features['district'].copy() if 'district' in features.columns else pd.Series(['未知']*len(features))
        self.original_data = features.copy()

        print(f"\n特征数量: {len(self.feature_names)}")
        print(f"特征列表: {self.feature_names}")
        print(f"特征矩阵形状: {self.X.shape}")
        print(f"目标变量形状: {self.y.shape}")

        # 计算各区县统计信息
        if 'district' in features.columns:
            district_stats = features.groupby('district')['total_price'].agg(['count', 'mean', 'std']).round(2)
            district_stats.columns = ['房源数量', '平均价格', '标准差']
            self.district_stats = district_stats.sort_values('房源数量', ascending=False)
            print(f"\n各区县统计信息 (前10):")
            print(self.district_stats.head(10))
            self.district_avg_prices = features.groupby('district')['total_price'].mean().round(2).to_dict()
        else:
            self.district_stats = pd.DataFrame()
            self.district_avg_prices = {}

        return self.X, self.y, self.districts

    def split_data_by_district(self, test_size=0.2, random_state=42):
        """按区县划分训练集和测试集（8:2比例）"""
        print(f"\n{'='*60}")
        print(f"3. 划分数据集（训练集:{int((1-test_size)*100)}% / 测试集:{int(test_size)*100}%）")
        print(f"{'='*60}")

        self.train_data = {}
        self.test_data = {}

        unique_districts = self.districts.unique()
        total_train = 0
        total_test = 0

        for district in unique_districts:
            district_mask = self.districts == district
            district_X = self.X[district_mask].copy()
            district_y = self.y[district_mask].copy()
            district_original = self.original_data[district_mask].copy()

            n_samples = len(district_X)

            if n_samples < 5:
                self.train_data[district] = {
                    'X': district_X, 'y': district_y, 'original': district_original
                }
                print(f"区县 {district}: 样本数 {n_samples} 过少，全部用于训练")
                total_train += n_samples
                continue

            X_train, X_test, y_train, y_test, original_train, original_test = train_test_split(
                district_X, district_y, district_original,
                test_size=test_size,
                random_state=random_state
            )

            self.train_data[district] = {
                'X': X_train, 'y': y_train, 'original': original_train
            }
            self.test_data[district] = {
                'X': X_test, 'y': y_test, 'original': original_test
            }

            train_count = len(X_train)
            test_count = len(X_test)
            total_train += train_count
            total_test += test_count

            print(f"\n区县 {district}:")
            print(f"  总样本: {n_samples}")
            print(f"  训练集: {train_count} ({train_count/n_samples*100:.1f}%)")
            print(f"  测试集: {test_count} ({test_count/n_samples*100:.1f}%)")

        print(f"\n总体统计:")
        print(f"  总训练集样本: {total_train}")
        print(f"  总测试集样本: {total_test}")
        print(f"  训练集比例: {total_train/(total_train+total_test)*100:.1f}%")
        print(f"  测试集比例: {total_test/(total_train+total_test)*100:.1f}%")

        return self.train_data, self.test_data

    def train_global_simple_model(self):
        """训练一个全局简单模型（用于样本少的区县）"""
        print(f"\n{'='*60}")
        print("训练全局简单模型（用于样本少的区县）")
        print(f"{'='*60}")

        X_train_list = []
        y_train_list = []

        for district, data in self.train_data.items():
            X_train_list.append(data['X'])
            y_train_list.append(data['y'])

        X_train_all = pd.concat(X_train_list)
        y_train_all = pd.concat(y_train_list)

        self.global_scaler = StandardScaler()
        numeric_cols = [col for col in self.numeric_features if col in X_train_all.columns]
        if numeric_cols:
            X_train_all[numeric_cols] = self.global_scaler.fit_transform(X_train_all[numeric_cols])

        self.global_simple_model = Ridge(alpha=10.0)
        self.global_simple_model.fit(X_train_all, y_train_all)

        y_pred = self.global_simple_model.predict(X_train_all)
        train_r2 = r2_score(y_train_all, y_pred)
        train_mae = mean_absolute_error(y_train_all, y_pred)

        print(f"全局简单模型 - 训练集 R2: {train_r2:.4f}, MAE: {train_mae:.2f}万")

        return self.global_simple_model

    def _get_models_by_sample_size(self, n_samples):
        """
        根据样本数返回合适的模型配置（仅五个标准模型，超参数自适应）
        始终返回字典，键为模型名称，值为模型实例
        """
        models = {}

        # Ridge (正则化强度随样本量调整)
        if n_samples < 30:
            alpha = 10.0
        elif n_samples < 50:
            alpha = 5.0
        else:
            alpha = 2.0
        models['Ridge'] = Ridge(alpha=alpha)

        # 决策树：样本量很小时限制深度
        if n_samples >= 30:
            if n_samples < 50:
                models['决策树'] = DecisionTreeRegressor(max_depth=3, random_state=42)
            else:
                max_depth = min(6, max(3, n_samples // 20))
                min_samples_split = max(5, n_samples // 30)
                min_samples_leaf = max(2, n_samples // 40)
                models['决策树'] = DecisionTreeRegressor(
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    max_features='sqrt',
                    random_state=42
                )

        # 随机森林：样本量 >=30 时启用
        if n_samples >= 30:
            if n_samples < 50:
                models['随机森林'] = RandomForestRegressor(
                    n_estimators=30, max_depth=4, random_state=42, n_jobs=-1
                )
            else:
                max_depth = min(6, max(3, n_samples // 20))
                min_samples_split = max(5, n_samples // 30)
                min_samples_leaf = max(2, n_samples // 40)
                models['随机森林'] = RandomForestRegressor(
                    n_estimators=50,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    max_features='sqrt',
                    random_state=42,
                    n_jobs=-1
                )

        # 梯度提升
        if n_samples >= 30:
            if n_samples < 50:
                models['梯度提升'] = GradientBoostingRegressor(
                    n_estimators=30, max_depth=3, learning_rate=0.05, random_state=42
                )
            else:
                max_depth = min(4, max(2, n_samples // 30))
                min_samples_split = max(5, n_samples // 30)
                min_samples_leaf = max(2, n_samples // 40)
                models['梯度提升'] = GradientBoostingRegressor(
                    n_estimators=50,
                    max_depth=max_depth,
                    learning_rate=0.05,
                    subsample=0.8,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    random_state=42
                )

        # XGBoost
        if XGB_AVAILABLE and n_samples >= 30:
            if n_samples < 50:
                models['XGBoost'] = xgb.XGBRegressor(
                    n_estimators=30, max_depth=3, learning_rate=0.05, random_state=42, n_jobs=-1
                )
            else:
                max_depth = min(4, max(2, n_samples // 30))
                models['XGBoost'] = xgb.XGBRegressor(
                    n_estimators=50,
                    max_depth=max_depth,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=1.0,
                    reg_lambda=2.0,
                    random_state=42,
                    n_jobs=-1
                )

        # 如果 models 为空（n_samples<30 且未添加树模型），则只保留 Ridge
        if not models:
            models['Ridge'] = Ridge(alpha=10.0)

        return models

    def train_by_district(self):
        """按区县分别训练模型，并记录所有候选模型性能（仅五模型 + 平均价格基准）"""
        print(f"\n{'='*60}")
        print("4. 按区县分别训练模型（记录所有候选模型性能）")
        print(f"{'='*60}")

        self.train_global_simple_model()
        trained_count = 0

        for district in self.train_data.keys():
            train_info = self.train_data[district]
            X_train = train_info['X'].copy()
            y_train = train_info['y'].copy()
            n_samples = len(X_train)

            # 初始化该区县的性能字典
            self.all_models_performance[district] = {}

            if n_samples < 10:
                # 使用全局模型
                self.district_models[district] = {
                    'best_model': self.global_simple_model,
                    'best_model_name': '全局Ridge模型',
                    'scaler': self.global_scaler,
                    'feature_names': self.feature_names,
                    'numeric_features': self.numeric_features,
                    'n_samples': n_samples,
                    'avg_price': self.district_avg_prices.get(district, 0),
                    'cv_mean': 0,
                    'train_r2': 0,
                    'train_mae': 0,
                    'use_global': True
                }
                self.all_models_performance[district]['全局Ridge模型'] = {
                    'train_mae': 0,
                    'train_r2': 0,
                    'cv_r2': 0,
                    'status': '使用全局模型（样本极少）'
                }
                trained_count += 1
                continue

            print(f"\n正在训练区县: {district} (训练样本: {n_samples})")

            # 标准化
            scaler = StandardScaler()
            numeric_cols = [col for col in self.numeric_features if col in X_train.columns]
            if numeric_cols:
                X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])

            # 获取五模型
            models = self._get_models_by_sample_size(n_samples)
            district_models = {}

            # 平均价格基准（始终作为参比）
            avg_price = self.district_avg_prices.get(district, y_train.mean())
            train_mae_avg = mean_absolute_error(y_train, [avg_price] * len(y_train))
            district_models['平均价格'] = {
                'model': None,
                'cv_mean': 0,
                'cv_std': 0,
                'train_r2': 0,
                'train_mae': train_mae_avg,
                'is_avg_model': True,
                'avg_price': avg_price
            }
            self.all_models_performance[district]['平均价格'] = {
                'train_mae': train_mae_avg,
                'train_r2': 0,
                'cv_r2': 0,
                'status': '基准模型（区县均值）'
            }
            print(f"  ✓ 平均价格: MAE={train_mae_avg:.2f}万")

            # 训练各模型
            for name, model in models.items():
                try:
                    cv_folds = min(3, max(2, n_samples // 5))
                    cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='r2')
                    cv_mean = cv_scores.mean()
                    cv_std = cv_scores.std()

                    model.fit(X_train, y_train)
                    y_train_pred = model.predict(X_train)
                    train_r2 = r2_score(y_train, y_train_pred)
                    train_mae = mean_absolute_error(y_train, y_train_pred)

                    overfitting_threshold = 0.3 if n_samples < 50 else 0.2
                    overfitting = train_r2 - cv_mean

                    self.all_models_performance[district][name] = {
                        'train_mae': train_mae,
                        'train_r2': train_r2,
                        'cv_r2': cv_mean,
                        'cv_std': cv_std,
                        'overfitting': overfitting,
                        'status': '通过' if overfitting < overfitting_threshold else '过拟合过滤'
                    }

                    if overfitting < overfitting_threshold:
                        district_models[name] = {
                            'model': model,
                            'cv_mean': cv_mean,
                            'cv_std': cv_std,
                            'train_r2': train_r2,
                            'train_mae': train_mae,
                            'overfitting': overfitting
                        }
                        print(f"  ✓ {name}: cv_r2={cv_mean:.4f} (+/- {cv_std*2:.4f}), train_mae={train_mae:.2f}万")
                    else:
                        print(f"  ✗ {name}: 过拟合 (overfitting={overfitting:.4f})，已过滤")
                except Exception as e:
                    print(f"  ✗ {name} 训练失败: {e}")
                    continue

            if district_models:
                # 选择最佳模型：优先选 CV R2 最高的（排除平均价格）
                candidate_models = {k: v for k, v in district_models.items() if not v.get('is_avg_model', False)}
                if candidate_models:
                    best_model_name = max(candidate_models, key=lambda x: candidate_models[x]['cv_mean'])
                    best_model_info = candidate_models[best_model_name]
                else:
                    best_model_name = '平均价格'
                    best_model_info = district_models['平均价格']

                self.district_models[district] = {
                    'best_model': best_model_info.get('model'),
                    'best_model_name': best_model_name,
                    'all_models': district_models,
                    'scaler': scaler,
                    'feature_names': self.feature_names,
                    'numeric_features': self.numeric_features,
                    'n_samples': n_samples,
                    'avg_price': avg_price,
                    'cv_mean': best_model_info.get('cv_mean', 0),
                    'cv_std': best_model_info.get('cv_std', 0),
                    'train_r2': best_model_info.get('train_r2', 0),
                    'train_mae': best_model_info.get('train_mae', 0),
                    'is_avg_model': best_model_info.get('is_avg_model', False)
                }
                self.district_scalers[district] = scaler

                print(f"  ✅ 最佳模型: {best_model_name}")
                if 'cv_mean' in best_model_info:
                    print(f"     交叉验证 R2: {best_model_info['cv_mean']:.4f}")
                print(f"     训练集 MAE: {best_model_info['train_mae']:.2f}万")
                trained_count += 1
            else:
                # 没有任何模型通过过拟合检查，使用全局模型
                self.district_models[district] = {
                    'best_model': self.global_simple_model,
                    'best_model_name': '全局Ridge模型（无合格模型）',
                    'scaler': self.global_scaler,
                    'n_samples': n_samples,
                    'avg_price': avg_price,
                    'use_global': True
                }
                self.all_models_performance[district]['全局Ridge模型（回退）'] = {
                    'train_mae': 0,
                    'train_r2': 0,
                    'cv_r2': 0,
                    'status': '所有本地模型均过拟合，回退全局模型'
                }
                print(f"  ⚠️  所有本地模型过拟合，使用全局模型")

        print(f"\n{'='*60}")
        print(f"按区县训练完成: {trained_count} 个区县")
        return self.district_models

    def validate_on_test_set(self):
        """在测试集上验证模型"""
        print(f"\n{'='*60}")
        print("5. 测试集验证（与真实数据对比）")
        print(f"{'='*60}")

        validation_results = []
        all_actual = []
        all_predicted = []
        district_errors = []

        for district, model_info in self.district_models.items():
            if district not in self.test_data:
                continue

            test_info = self.test_data[district]
            X_test = test_info['X'].copy()
            y_test = test_info['y'].copy()
            original_test = test_info['original']

            n_test = len(y_test)
            if n_test == 0:
                continue

            if model_info.get('scaler') is not None:
                numeric_cols = [col for col in self.numeric_features if col in X_test.columns]
                if numeric_cols:
                    X_test[numeric_cols] = model_info['scaler'].transform(X_test[numeric_cols])

            if model_info.get('is_avg_model', False):
                y_pred = np.full_like(y_test, model_info['avg_price'])
            else:
                y_pred = model_info['best_model'].predict(X_test)

            test_r2 = r2_score(y_test, y_pred)
            test_mae = mean_absolute_error(y_test, y_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            rel_errors = np.abs((y_test - y_pred) / y_test) * 100
            median_rel_error = np.median(rel_errors)

            self.district_models[district]['test_r2'] = test_r2
            self.district_models[district]['test_mae'] = test_mae
            self.district_models[district]['test_rmse'] = test_rmse
            self.district_models[district]['median_rel_error'] = median_rel_error

            all_actual.extend(y_test.values)
            all_predicted.extend(y_pred)
            district_errors.append({
                'district': district,
                'mae': test_mae,
                'median_rel_error': median_rel_error,
                'n_test': n_test
            })

            print(f"\n区县: {district} (测试集样本数: {n_test})")
            print(f"  模型: {model_info['best_model_name']}")
            print(f"  测试集表现:")
            print(f"    R2: {test_r2:.4f}")
            print(f"    MAE: {test_mae:.2f}万")
            print(f"    相对误差中位数: {median_rel_error:.1f}%")

            n_show = min(2, n_test)
            indices = np.random.choice(n_test, n_show, replace=False)
            print(f"\n  随机样本详细对比:")
            for i, idx in enumerate(indices, 1):
                actual = y_test.values[idx]
                predicted = y_pred[idx]
                error = abs(actual - predicted)
                error_percent = error / actual * 100

                original_row = original_test.iloc[idx]
                area = original_row.get('area', 0)
                rooms = original_row.get('rooms', '未知')

                print(f"\n    样本 {i}:")
                print(f"      面积: {area:.1f}㎡, 户型: {rooms}室")
                print(f"      实际价格: {actual:.2f}万")
                print(f"      预测价格: {predicted:.2f}万")
                print(f"      绝对误差: {error:.2f}万")
                print(f"      相对误差: {error_percent:.1f}%")

            validation_results.append({
                'district': district,
                'model': model_info['best_model_name'],
                'test_r2': test_r2,
                'test_mae': test_mae,
                'median_rel_error': median_rel_error,
                'n_samples': n_test
            })

        if all_actual:
            overall_r2 = r2_score(all_actual, all_predicted)
            overall_mae = mean_absolute_error(all_actual, all_predicted)
            overall_rmse = np.sqrt(mean_squared_error(all_actual, all_predicted))

            # 保存总体指标供可视化使用
            self.overall_metrics = {
                'r2': overall_r2,
                'mae': overall_mae,
                'rmse': overall_rmse,
                'n_samples': len(all_actual)
            }

            district_errors.sort(key=lambda x: x['mae'])

            print(f"\n{'='*60}")
            print(f"总体测试集表现:")
            print(f"  总测试样本数: {len(all_actual)}")
            print(f"  总体 R2: {overall_r2:.4f}")
            print(f"  总体 MAE: {overall_mae:.2f}万")
            print(f"  总体 RMSE: {overall_rmse:.2f}万")

            print(f"\n各区县MAE排名 (从小到大):")
            for i, d in enumerate(district_errors[:5], 1):
                print(f"  {i}. {d['district']}: MAE={d['mae']:.2f}万, 中位相对误差={d['median_rel_error']:.1f}%")
            if len(district_errors) > 5:
                print("  ...")
                for d in district_errors[-3:]:
                    print(f"  ✗ {d['district']}: MAE={d['mae']:.2f}万, 中位相对误差={d['median_rel_error']:.1f}%")

        return validation_results

    def predict_by_district(self, district, features_dict):
        """根据区县预测房价"""
        if district not in self.district_models:
            if self.global_simple_model is not None:
                features = self._build_features(features_dict)
                features_df = pd.DataFrame([features], columns=self.feature_names)
                numeric_cols = [col for col in self.numeric_features if col in features_df.columns]
                if numeric_cols and self.global_scaler is not None:
                    features_df[numeric_cols] = self.global_scaler.transform(features_df[numeric_cols])
                prediction = self.global_simple_model.predict(features_df)[0]
                avg_price = self.district_avg_prices.get(district, 0)
                if prediction < 0 or prediction > avg_price * 3:
                    prediction = avg_price
                return {
                    'model': '全局Ridge模型',
                    'predicted_price': round(prediction, 2),
                    'unit_price': round(prediction / features_dict.get('area', 1) * 10000, 2),
                    'district_avg': avg_price,
                    'note': '使用全局模型（无专门区县模型）'
                }
            else:
                avg_price = self.district_avg_prices.get(district, 0)
                return {
                    'model': '区县平均价格',
                    'predicted_price': avg_price,
                    'unit_price': avg_price / features_dict.get('area', 1) * 10000 if avg_price > 0 else 0,
                    'note': '使用区县平均价格'
                }

        model_info = self.district_models[district]

        if model_info.get('is_avg_model', False):
            prediction = model_info['avg_price']
            model_name = '区县平均价格'
        else:
            features = self._build_features(features_dict)
            features_df = pd.DataFrame([features], columns=self.feature_names)
            if model_info.get('scaler') is not None:
                numeric_cols = [col for col in self.numeric_features if col in features_df.columns]
                if numeric_cols:
                    features_df[numeric_cols] = model_info['scaler'].transform(features_df[numeric_cols])
            prediction = model_info['best_model'].predict(features_df)[0]
            model_name = model_info['best_model_name']

        avg_price = model_info['avg_price']
        if prediction < 0 or prediction > avg_price * 3:
            prediction = avg_price
            model_name = f"{model_name} (修正)"

        area = features_dict.get('area', 1)
        unit_price = round(prediction / area * 10000, 2) if area > 0 else 0

        return {
            'model': model_name,
            'predicted_price': round(prediction, 2),
            'unit_price': unit_price,
            'district_avg': avg_price,
            'model_cv': model_info.get('cv_mean', 0),
            'model_test_r2': model_info.get('test_r2', 0),
            'model_test_mae': model_info.get('test_mae', 0)
        }

    def _build_features(self, features_dict):
        features = []
        for feature in self.feature_names:
            if feature in self.numeric_features:
                val = features_dict.get(feature, 0)
                features.append(float(val))
            elif feature.endswith('_encoded'):
                original_feature = feature.replace('_encoded', '')
                val = features_dict.get(original_feature, '')
                le = self.label_encoders.get(original_feature)
                if le and val:
                    try:
                        encoded = le.transform([str(val)])[0]
                    except:
                        encoded = 0
                else:
                    encoded = 0
                features.append(encoded)
            else:
                val = features_dict.get(feature, 0)
                features.append(int(val))
        return features

    def display_model_performance(self, min_samples=10, save_csv=True):
        """展示每个区县所有候选模型的性能指标，并绘图（仅保留MAE和R2柱状图）"""
        print(f"\n{'='*60}")
        print("模型性能对比（训练阶段）")
        print(f"{'='*60}")

        # 构建DataFrame
        rows = []
        for district, models in self.all_models_performance.items():
            n_samples = self.district_models.get(district, {}).get('n_samples', 0)
            for model_name, metrics in models.items():
                row = {
                    '区县': district,
                    '样本数': n_samples,
                    '模型': model_name,
                    '训练MAE(万元)': metrics.get('train_mae', np.nan),
                    '训练R2': metrics.get('train_r2', np.nan),
                    '交叉验证R2': metrics.get('cv_r2', np.nan),
                    '状态': metrics.get('status', '')
                }
                rows.append(row)

        if not rows:
            print("没有模型性能数据可展示")
            return

        df_perf = pd.DataFrame(rows)
        df_perf = df_perf.sort_values(['样本数', '区县', '模型'], ascending=[False, True, True])

        print("\n所有候选模型性能汇总（部分列）:")
        print(df_perf[['区县', '样本数', '模型', '训练MAE(万元)', '交叉验证R2', '状态']].to_string(index=False))

        if save_csv:
            csv_path = 'model_performance_summary.csv'
            df_perf.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n性能汇总表已保存至: {csv_path}")

        # ========== 可视化部分 ==========
        # 筛选样本数≥min_samples 且至少有两个候选模型的区县（用于柱状图）
        districts_to_plot = [d for d in df_perf['区县'].unique()
                             if self.district_models.get(d, {}).get('n_samples', 0) >= min_samples]
        if len(districts_to_plot) == 0:
            print(f"没有样本数≥{min_samples}的区县，跳过绘图")
            return

        # 准备绘图数据（仅包含五个标准模型，忽略平均价格和全局模型）
        standard_models = ['Ridge', '决策树', '随机森林', '梯度提升', 'XGBoost']
        plot_data = {}
        for district in districts_to_plot:
            district_df = df_perf[df_perf['区县'] == district]
            # 只保留标准模型
            district_df = district_df[district_df['模型'].isin(standard_models)]
            district_df = district_df[district_df['训练MAE(万元)'].notna()]
            if len(district_df) < 2:
                continue
            plot_data[district] = district_df.set_index('模型')[['训练MAE(万元)', '交叉验证R2']].to_dict('index')

        if not plot_data:
            print("没有足够数据绘图（需要至少2个标准模型）")
            return

        # 图1：训练MAE对比柱状图
        fig1, ax1 = plt.subplots(figsize=(14, max(4, len(plot_data)*0.4)))
        all_models = sorted([m for m in standard_models if any(m in d for d in plot_data.values())])
        districts = list(plot_data.keys())
        mae_matrix = []
        for district in districts:
            row = [plot_data[district].get(model, {}).get('训练MAE(万元)', np.nan) for model in all_models]
            mae_matrix.append(row)
        mae_matrix = np.array(mae_matrix).T
        x = np.arange(len(districts))
        width = 0.8 / len(all_models) if len(all_models) > 0 else 0.1
        for i, model in enumerate(all_models):
            ax1.bar(x + i*width, mae_matrix[i], width, label=model)
        ax1.set_xticks(x + width*(len(all_models)-1)/2)
        ax1.set_xticklabels(districts, rotation=45, ha='right')
        ax1.set_ylabel('训练 MAE (万元)')
        ax1.set_title('各模型训练 MAE 对比（样本数≥10）')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('training_mae_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("训练MAE对比图已保存至: training_mae_comparison.png")

        # 图2：交叉验证R2对比柱状图
        fig2, ax2 = plt.subplots(figsize=(14, max(4, len(plot_data)*0.4)))
        cv_matrix = []
        for district in districts:
            row = [plot_data[district].get(model, {}).get('交叉验证R2', np.nan) for model in all_models]
            cv_matrix.append(row)
        cv_matrix = np.array(cv_matrix).T
        for i, model in enumerate(all_models):
            ax2.bar(x + i*width, cv_matrix[i], width, label=model)
        ax2.set_xticks(x + width*(len(all_models)-1)/2)
        ax2.set_xticklabels(districts, rotation=45, ha='right')
        ax2.set_ylabel('交叉验证 R2')
        ax2.set_title('各模型交叉验证 R2 对比（样本数≥10）')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('cv_r2_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("交叉验证R2对比图已保存至: cv_r2_comparison.png")

    def plot_test_results(self, save_path='test_results.png'):
        """可视化测试结果（包含MAE、RMSE、相对误差、样本数关系）"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))

        districts = []
        test_mae = []
        test_rmse = []
        rel_errors = []
        n_samples = []

        for district, info in self.district_models.items():
            if 'test_mae' in info:
                districts.append(district)
                test_mae.append(info['test_mae'])
                test_rmse.append(info.get('test_rmse', 0))
                rel_errors.append(info.get('median_rel_error', 0))
                n_samples.append(info['n_samples'])

        if not districts:
            print("没有测试结果可可视化")
            return

        # 按 MAE 排序
        sorted_idx = np.argsort(test_mae)
        sorted_districts = [districts[i] for i in sorted_idx]
        sorted_mae = [test_mae[i] for i in sorted_idx]
        sorted_rmse = [test_rmse[i] for i in sorted_idx]
        sorted_rel = [rel_errors[i] for i in sorted_idx]
        sorted_samples = [n_samples[i] for i in sorted_idx]

        # 子图1：MAE
        bars1 = axes[0, 0].barh(range(len(sorted_districts)), sorted_mae)
        axes[0, 0].set_yticks(range(len(sorted_districts)))
        axes[0, 0].set_yticklabels(sorted_districts)
        axes[0, 0].set_xlabel('MAE (万元)')
        axes[0, 0].set_title('各区县测试集 MAE (从小到大)')
        for bar, mae in zip(bars1, sorted_mae):
            if mae < 10:
                bar.set_color('green')
            elif mae < 20:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        axes[0, 0].grid(True, alpha=0.3)

        # 子图2：RMSE
        bars2 = axes[0, 1].barh(range(len(sorted_districts)), sorted_rmse)
        axes[0, 1].set_yticks(range(len(sorted_districts)))
        axes[0, 1].set_yticklabels(sorted_districts)
        axes[0, 1].set_xlabel('RMSE (万元)')
        axes[0, 1].set_title('各区县测试集 RMSE (从小到大)')
        for bar, rmse in zip(bars2, sorted_rmse):
            if rmse < 20:
                bar.set_color('green')
            elif rmse < 40:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        axes[0, 1].grid(True, alpha=0.3)

        # 子图3：相对误差中位数
        axes[0, 2].barh(range(len(sorted_districts)), sorted_rel)
        axes[0, 2].set_yticks(range(len(sorted_districts)))
        axes[0, 2].set_yticklabels(sorted_districts)
        axes[0, 2].set_xlabel('相对误差中位数 (%)')
        axes[0, 2].set_title('各区县相对误差中位数')
        axes[0, 2].grid(True, alpha=0.3)

        # 子图4：训练样本数
        axes[1, 0].barh(range(len(sorted_districts)), sorted_samples)
        axes[1, 0].set_yticks(range(len(sorted_districts)))
        axes[1, 0].set_yticklabels(sorted_districts)
        axes[1, 0].set_xlabel('样本数')
        axes[1, 0].set_title('各区县训练样本数')
        axes[1, 0].grid(True, alpha=0.3)

        # 子图5：MAE vs 样本数散点图
        axes[1, 1].scatter(n_samples, test_mae, alpha=0.6)
        for i, district in enumerate(districts):
            axes[1, 1].annotate(district, (n_samples[i], test_mae[i]), fontsize=8)
        axes[1, 1].set_xlabel('训练样本数')
        axes[1, 1].set_ylabel('测试集 MAE (万元)')
        axes[1, 1].set_title('MAE vs 样本数')
        axes[1, 1].grid(True, alpha=0.3)

        # 子图6：RMSE vs 样本数散点图
        axes[1, 2].scatter(n_samples, test_rmse, alpha=0.6, color='purple')
        for i, district in enumerate(districts):
            axes[1, 2].annotate(district, (n_samples[i], test_rmse[i]), fontsize=8)
        axes[1, 2].set_xlabel('训练样本数')
        axes[1, 2].set_ylabel('测试集 RMSE (万元)')
        axes[1, 2].set_title('RMSE vs 样本数')
        axes[1, 2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n测试结果图表（含MAE、RMSE）已保存到: {save_path}")
        plt.show()

        # 额外绘制总体性能柱状图
        if hasattr(self, 'overall_metrics'):
            fig_overall, ax_overall = plt.subplots(figsize=(6, 4))
            metrics = ['MAE (万元)', 'RMSE (万元)', 'R2']
            values = [self.overall_metrics['mae'], self.overall_metrics['rmse'], self.overall_metrics['r2']]
            ax_overall.bar(metrics, values, color=['steelblue', 'lightcoral', 'seagreen'])
            ax_overall.set_ylabel('值')
            ax_overall.set_title(f'总体预测性能 (测试样本数={self.overall_metrics["n_samples"]})')
            for i, v in enumerate(values):
                ax_overall.text(i, v + 0.01, f"{v:.3f}", ha='center')
            plt.tight_layout()
            plt.savefig('overall_performance.png', dpi=300)
            plt.show()
            print("总体性能图已保存至: overall_performance.png")

    def save_results(self, output_dir='model_results'):
        """保存结果和模型"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        test_results = []
        for district, info in self.district_models.items():
            test_results.append({
                'district': district,
                'best_model': info['best_model_name'],
                'n_samples': info['n_samples'],
                'avg_price': info['avg_price'],
                'train_mae': info.get('train_mae', 0),
                'test_r2': info.get('test_r2', 0),
                'test_mae': info.get('test_mae', 0),
                'median_rel_error': info.get('median_rel_error', 0)
            })

        df_results = pd.DataFrame(test_results)
        df_results = df_results.sort_values('test_mae')
        results_path = os.path.join(output_dir, f'test_results_{timestamp}.csv')
        df_results.to_csv(results_path, index=False, encoding='utf-8-sig')

        # 保存完整模型
        model_path = os.path.join(output_dir, f'all_models_{timestamp}.pkl')
        joblib.dump({
            'district_models': self.district_models,
            'district_scalers': self.district_scalers,
            'global_simple_model': self.global_simple_model,
            'global_scaler': self.global_scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'numeric_features': self.numeric_features,
            'district_avg_prices': self.district_avg_prices,
            'test_results': test_results,
            'all_models_performance': self.all_models_performance
        }, model_path)

        print(f"\n结果已保存:")
        print(f"  测试结果CSV: {results_path}")
        print(f"  完整模型: {model_path}")

        return results_path

    def run_complete_analysis(self, save_results=True):
        """运行完整分析"""
        print(f"\n{'#'*80}")
        print("# 开始按区县分类的房价预测分析（样本量自适应 + 五模型对比 + 指标可视化）")
        print(f"{'#'*80}")

        self.prepare_features()
        self.split_data_by_district(test_size=0.2)
        self.train_by_district()
        self.validate_on_test_set()
        self.plot_test_results()
        self.display_model_performance(min_samples=10, save_csv=True)
        if save_results:
            self.save_results()

        return {
            'district_results': self.district_models,
            'test_results': self.validate_on_test_set()
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='按区县分类的房价预测（样本量自适应，五模型，指标可视化）')
    parser.add_argument('--csv', type=str, default='data\\clean_cleaned.csv', help='CSV文件路径')
    parser.add_argument('--no-save', action='store_true', help='不保存结果')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"错误: 文件不存在 {args.csv}")
        return

    predictor = MultiModelHousePricePredictor(args.csv)
    results = predictor.run_complete_analysis(save_results=not args.no_save)

    # 示例预测（可选）
    print("\n分析完成。所有图表已生成。")

if __name__ == '__main__':
    main()