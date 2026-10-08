import os
import joblib
import pickle
import glob
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class _ModelManager:
    def __init__(self):
        self.district_models = {}
        self.district_avg_prices = {}
        self.overall_mae = 0
        self._load_latest_models()

    def _load_latest_models(self):
        base_dir = os.path.dirname(__file__)
        results_dir = os.path.join(base_dir, 'model_results')
        if not os.path.isdir(results_dir):
            # Fallback: if the script was run from backend root, models may be saved in backend/model_results
            results_dir = os.path.join(os.path.dirname(base_dir), 'model_results')
            if not os.path.isdir(results_dir):
                logger.warning('model_results directory not found in prediction or backend root')
                return
            logger.info(f'using fallback model_results directory: {results_dir}')

        pkls = sorted(glob.glob(os.path.join(results_dir, '*.pkl')))
        if not pkls:
            logger.warning(f'no .pkl model files found in model_results at {results_dir}')
            return

        latest = pkls[-1]
        logger.info(f'loading model file: {latest}')
        try:
            data = joblib.load(latest)
        except Exception:
            try:
                with open(latest, 'rb') as f:
                    data = pickle.load(f)
            except Exception as e:
                logger.exception('failed to load model file')
                return

        # Try to extract expected attributes from loaded object
        if isinstance(data, dict):
            self.district_models = data.get('district_models', {})
            self.district_avg_prices = data.get('district_avg_prices', {})
            self.overall_mae = data.get('overall_mae', 0)
        else:
            # Assume it's an object with attributes
            self.district_models = getattr(data, 'district_models', {}) or {}
            self.district_avg_prices = getattr(data, 'district_avg_prices', {}) or {}
            self.overall_mae = getattr(data, 'overall_mae', 0)

    def predict_by_district(self, district, features: dict):
        """返回预测结果字典：{'unit_price':..., 'total_price':...} """
        # if no district model, fallback to average
        if district not in self.district_models:
            avg = self.district_avg_prices.get(district)
            if avg is None:
                raise ValueError(f'没有可用的模型或均价用于区县: {district}')
            # 仅返回平均总价，无法计算单价
            return {'unit_price': round(avg / max(features.get('area', 1), 1), 2), 'total_price': round(avg, 2)}

        model_info = self.district_models[district]

        model = model_info.get('best_model') or model_info.get('best_model_obj')
        feature_names = model_info.get('feature_names') or model_info.get('feature_list')

        if model is None or feature_names is None:
            # fallback to average
            avg = self.district_avg_prices.get(district, 0)
            return {'unit_price': round(avg / max(features.get('area', 1), 1), 2), 'total_price': round(avg, 2)}

        # Build DataFrame in expected order
        X = pd.DataFrame([{k: features.get(k, 0) for k in feature_names}])

        # If a scaler is provided, try to apply
        scaler = model_info.get('scaler')
        try:
            if scaler is not None:
                numeric_cols = [c for c in feature_names if c in ('unit_price', 'area')]
                if numeric_cols:
                    X[numeric_cols] = scaler.transform(X[numeric_cols])
        except Exception:
            # ignore scaler errors
            logger.exception('scaler transform failed')

        try:
            pred = model.predict(X.values)
            if isinstance(pred, (list, tuple, np.ndarray)):
                total_price = float(pred[0])
            else:
                total_price = float(pred)

            # 如果预测结果出现负数或异常极端值，进行后处理
            district_avg = self.district_avg_prices.get(district, 0.0)
            if district_avg > 0:
                lower_bound = max(1.0, district_avg * 0.4)
                upper_bound = max(district_avg * 3.5, district_avg + 50.0)
                if total_price < lower_bound:
                    total_price = lower_bound
                elif total_price > upper_bound:
                    total_price = upper_bound
            else:
                total_price = max(total_price, 1.0)

            # 数据集中 total_price 使用的是 万（单位：万元），前端显示单价需要 元/㎡
            area = max(float(features.get('area', 1)), 1.0)
            try:
                # total_price is in 万 -> convert to 元
                total_price_wan = total_price
                total_price_yuan = total_price_wan * 10000.0
                unit_price_yuan_per_m2 = total_price_yuan / area
                unit_price = round(unit_price_yuan_per_m2, 2)
                return {
                    'unit_price': unit_price,
                    'total_price': round(total_price_wan, 2),
                    'note': '后处理已应用：负值/极端值已修正'
                }
            except Exception:
                # fallback: return naive division (万/㎡)
                unit_price = round(total_price / area, 2)
                return {
                    'unit_price': unit_price,
                    'total_price': round(total_price, 2),
                    'note': '后处理已应用：负值/极端值已修正'
                }
        except Exception:
            logger.exception('model prediction failed')
            avg = self.district_avg_prices.get(district, 0)
            return {'unit_price': round(avg / max(features.get('area', 1), 1), 2), 'total_price': round(avg, 2)}


# single shared instance
model_manager = _ModelManager()
