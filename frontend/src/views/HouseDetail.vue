<template>
  <div class="house-detail-page">
    <div class="header">
      <button class="back-btn" @click="$router.back()">返回</button>
      <h1 class="title">{{ house?.title || '房源详情' }}</h1>
      <span v-if="house?.district || house?.community" class="sub-title">
        {{ house?.district || '' }} {{ house?.community || '' }}
      </span>
    </div>

    <div class="content">
      <div class="info-panel" v-if="house">
        <h2 class="section-title">房源信息</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">总价</span>
            <span class="value highlight">{{ house.total_price }} 万</span>
          </div>
          <div class="info-item">
            <span class="label">单价</span>
            <span class="value">{{ house.unit_price ? Math.round(house.unit_price) + ' 元/㎡' : '暂无' }}</span>
          </div>
          <div class="info-item">
            <span class="label">户型</span>
            <span class="value">{{ house.rooms }}室{{ house.halls }}厅</span>
          </div>
          <div class="info-item">
            <span class="label">建筑面积</span>
            <span class="value">{{ house.area }} ㎡</span>
          </div>
          <div class="info-item">
            <span class="label">所在区域</span>
            <span class="value">{{ house.city || '' }} {{ house.district || '' }}</span>
          </div>
          <div class="info-item">
            <span class="label">小区</span>
            <span class="value">{{ house.community || '暂无' }}</span>
          </div>
          <div class="info-item address-item">
            <span class="label">详细地址</span>
            <span class="value">{{ house.address || '暂无' }}</span>
          </div>
        </div>
      </div>

      <div class="map-panel">
        <div class="map-header">
          <h2 class="section-title">位置与路线</h2>
          <div class="map-actions">
            <button class="action-btn" @click="replanRoute" :disabled="!destination">
              重新规划路线
            </button>
            <button class="action-btn secondary" @click="openExternalAmap" :disabled="!destination">
              在高德地图中打开
            </button>
          </div>
        </div>

        <div class="map-container">
          <div id="map" class="map"></div>

          <!-- 当前目的地信息 -->
          <div v-if="currentLocation" class="location-info">
            <h3>目的地</h3>
            <p><strong>地址:</strong> {{ currentLocation.address }}</p>
            <p><strong>经纬度:</strong> {{ currentLocation.lng }}, {{ currentLocation.lat }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { listingsApi } from '@/api/listings'

export default {
  name: 'SimpleMapView',
  data() {
    return {
      // 当前房源信息
      house: null,

      // 当前目标位置（房源坐标）
      destination: null,

      // 地图上当前展示的位置信息（用于右侧信息卡片）
      currentLocation: null,
      
      // 地图相关
      map: null,
      AMap: null,
      markers: [],
      
      // 收藏的位置
      bookmarks: [],
      
      // 用户位置
      userLocation: null
    }
  },
  
  mounted() {
    console.log('[Map] HouseDetail mounted, route params:', this.$route.params, 'query:', this.$route.query)
    this.initMap()
    this.loadBookmarks()
    this.tryAutoNavigateFromRoute()
  },
  
  methods: {
    // 初始化地图
    async initMap() {
      try {
        // 动态加载高德地图JS API
        await this.loadAMap()
        
        // 初始化地图
        this.map = new this.AMap.Map('map', {
          zoom: 11,
          center: [104.065735, 30.659462], // 成都市中心
          viewMode: '3D'
        })

        // 添加地图点击事件
        this.map.on('click', (e) => {
          this.reverseGeocode(e.lnglat)
        })
        
      } catch (error) {
        console.error('地图初始化失败:', error)
        alert('地图加载失败，请刷新页面重试')
      }
    },

    // 动态加载高德地图JS API
    loadAMap() {
      return new Promise((resolve, reject) => {
        if (window.AMap) {
          this.AMap = window.AMap
          resolve()
          return
        }

        const script = document.createElement('script')
        // 使用项目内的高德 API Key（Web 端 JSAPI）
        const AMAP_KEY = '50ae835ae0e54323e91f9d0ddf18b4ec'

        // 按高德 JSAPI v2 文档，在加载脚本前通过全局变量配置安全密钥
        // 注意：这里的 securityJsCode 必须是“Web 端”这条 key 下的 JSAPI 安全密钥
        window._AMapSecurityConfig = {
          securityJsCode: 'bb944f3dfc352597bcd5b0aa391c6f88'
        }

        script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}&plugin=AMap.Geocoder,AMap.Geolocation,AMap.ToolBar,AMap.Scale,AMap.Driving`
        script.onload = () => {
          // 有些情况下高德会返回 key 错误，脚本仍然可能加载但 window.AMap 不存在
          if (window.AMap) {
            this.AMap = window.AMap
            resolve()
          } else {
            reject(new Error('AMAP_NOT_AVAILABLE'))
          }
        }
        script.onerror = reject
        document.head.appendChild(script)
      })
    },

    // 获取路由中的房源 id 并自动触发导航流程（若存在）
    async tryAutoNavigateFromRoute() {
      const id = this.$route.params.id || this.$route.query.id
      console.log('[Map] tryAutoNavigateFromRoute id =', id)
      if (!id) {
        console.warn('[Map] no house id from route, skip auto navigate')
        return
      }
      try {
        // 先从后端获取房源详情
        const res = await listingsApi.getHouseDetail(Number(id))
        const house = res
        this.house = house
        console.log('[Map] loaded house detail:', house)
        // 优先使用后端返回的经纬度字段（支持多种命名）
        const possibleLng = house.longitude || house.lng || house.lon || house.latlng?.[0] || house.经度 || house.lng_lat?.[0]
        const possibleLat = house.latitude || house.lat || house.latlng?.[1] || house.纬度 || house.lng_lat?.[1]

        let toLng = null
        let toLat = null
        if (possibleLng !== undefined && possibleLat !== undefined && possibleLng !== null && possibleLat !== null) {
          toLng = Number(possibleLng)
          toLat = Number(possibleLat)
        }

        // 当我们已有后端坐标时，先尝试加载 AMap；若加载失败则回退到打开外部高德地图标注
        let amapLoaded = false
        try {
          await this.loadAMap()
          amapLoaded = true
        } catch (e) {
          console.warn('AMap 加载失败，使用回退展示', e)
        }

        // 如果后端未提供经纬度，尝试使用地理编码（仅在 AMap 可用时）
        if ((toLng === null || toLat === null) && amapLoaded && (house.address || house.city)) {
          const address = house.address || ''
          const city = house.city || ''
          const geocoder = new this.AMap.Geocoder({ city: city || '全国' })
          geocoder.getLocation(address, (status, result) => {
            if (status === 'complete' && result.geocodes && result.geocodes.length > 0) {
              const loc = result.geocodes[0].location
              toLng = loc.lng
              toLat = loc.lat
              this.setDestination(toLng, toLat, house.title || address)
              this.navigateToHouse(toLng, toLat, house.title || address)
            } else {
              console.warn('房源地址地理编码未命中', address, result)
            }
          })
          return
        }

        if (toLng !== null && toLat !== null) {
          this.setDestination(toLng, toLat, house.title || house.address || '目的地')
          if (amapLoaded) {
            this.navigateToHouse(toLng, toLat, house.title || house.address || '目的地')
          } else {
            // 回退：打开外部高德地图标注页
            const uri = `https://uri.amap.com/marker?position=${toLng},${toLat}&name=${encodeURIComponent(house.title || house.address || '目的地')}&coordinate=gaode`
            window.open(uri, '_blank')
          }
        }
      } catch (e) {
        console.error('自动导航失败', e)
      }
    },

    // 用高德地图 URI 打开导航（在新窗口）
    openAmapNavigation(toLng, toLat, toName = '目的地') {
      if (!navigator.geolocation) {
        // 如果不能获取当前位置，则仅打开目的地定位页面
        const uri = `https://uri.amap.com/marker?position=${toLng},${toLat}&name=${encodeURIComponent(toName)}&coordinate=gaode`
        window.open(uri, '_blank')
        return
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const fromLng = pos.coords.longitude
          const fromLat = pos.coords.latitude
          // 高德导航 URI 格式：navigation
          const navUrl = `https://uri.amap.com/navigation?from=${fromLng},${fromLat},我的位置&to=${toLng},${toLat},${encodeURIComponent(toName)}&mode=car&policy=0&src=appname&coordinate=gaode&callnative=0`
          window.open(navUrl, '_blank')
        },
        (err) => {
          console.warn('获取用户位置失败，改为仅打开目的地', err)
          const uri = `https://uri.amap.com/marker?position=${toLng},${toLat}&name=${encodeURIComponent(toName)}&coordinate=gaode`
          window.open(uri, '_blank')
        },
        { timeout: 10000 }
      )
    },

    // 在当前地图上绘制从用户位置到目标位置的驾车路线（若无法定位则只标记目的地）
    async navigateToHouse(toLng, toLat, toName = '目的地') {
      try {
        const drawRoute = (fromLng, fromLat) => {
          // 调试：确认已经拿到起点坐标
          console.log('[Map] drawRoute from', fromLng, fromLat, 'to', toLng, toLat, toName)
          // 清除旧路线与标记
          this.clearMarkers()

          // 添加起点与终点标记
          const startMarker = new this.AMap.Marker({ position: [fromLng, fromLat], map: this.map, title: '我的位置' })
          const endMarker = new this.AMap.Marker({ position: [toLng, toLat], map: this.map, title: toName })
          this.markers.push(startMarker, endMarker)

          // 使用 Driving 在地图上绘制路线
          const driving = new this.AMap.Driving({ map: this.map })
          driving.search(
            [fromLng, fromLat],
            [toLng, toLat],
            (status, result) => {
              console.log('[Map] Driving.search status:', status, result)
              if (status === 'complete' && result && result.routes && result.routes.length > 0) {
                try {
                  this.map.setFitView()
                } catch (e) {
                  console.warn('fitView 失败', e)
                }
              } else {
                console.warn('[Map] 路线规划失败，回退为仅标记两点', status, result)
                try {
                  this.map.setFitView()
                } catch (e) {
                  console.warn('fitView 失败', e)
                }
              }
            }
          )
        }

        // 1. 优先使用高德 JS API 的定位插件（对 HTTPS 限制更友好，也支持 IP/WiFi 等）
        if (this.AMap && this.AMap.Geolocation) {
          const geolocation = new this.AMap.Geolocation({
            enableHighAccuracy: true,
            timeout: 10000,
            zoomToAccuracy: true
          })
          this.map.addControl(geolocation)

          geolocation.getCurrentPosition((status, result) => {
            console.log('[Map] AMap.Geolocation status:', status, result)
            if (status === 'complete' && result.position) {
              const fromLng = result.position.lng
              const fromLat = result.position.lat
              drawRoute(fromLng, fromLat)
            } else {
              console.warn('高德定位失败，回退到浏览器定位', status, result)
              this.fallbackBrowserLocation(toLng, toLat, toName, drawRoute)
            }
          })
          return
        }

        // 2. 如果没有高德定位插件，则使用浏览器原生 geolocation
        this.fallbackBrowserLocation(toLng, toLat, toName, drawRoute)
      } catch (e) {
        console.error('navigateToHouse 错误', e)
        // 出现异常时至少标记目的地
        const marker = new this.AMap.Marker({ position: [toLng, toLat], map: this.map, title: toName })
        this.markers.push(marker)
        this.map.setCenter([toLng, toLat])
        this.map.setZoom(15)
      }
    },

    // 使用浏览器 geolocation 的回退方案
    fallbackBrowserLocation(toLng, toLat, toName, drawRoute) {
      if (!navigator.geolocation) {
        console.warn('浏览器不支持地理位置，无法获取当前定位')
        const marker = new this.AMap.Marker({ position: [toLng, toLat], map: this.map, title: toName })
        this.markers.push(marker)
        this.map.setCenter([toLng, toLat])
        this.map.setZoom(15)
        return
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const fromLng = pos.coords.longitude
          const fromLat = pos.coords.latitude
          console.log('[Map] navigator.geolocation success:', fromLng, fromLat)
          drawRoute(fromLng, fromLat)
        },
        (err) => {
          console.warn('浏览器 geolocation 获取用户位置失败，仅标记目的地', err)
          const marker = new this.AMap.Marker({ position: [toLng, toLat], map: this.map, title: toName })
          this.markers.push(marker)
          this.map.setCenter([toLng, toLat])
          this.map.setZoom(15)
          // 提示用户检查浏览器定位权限/HTTPS
          alert('无法获取当前位置，请检查浏览器定位权限，或在 HTTPS/localhost 环境下打开系统。')
        },
        { timeout: 10000 }
      )
    },

    // 记录当前目的地
    setDestination(lng, lat, name) {
      this.destination = { lng, lat, name }
      // 同步到当前位置信息卡片
      this.currentLocation = {
        address: name,
        lng: lng.toFixed(6),
        lat: lat.toFixed(6)
      }
    },

    // 重新根据当前目的地进行路线规划
    replanRoute() {
      if (!this.destination || !this.AMap || !this.map) return
      this.navigateToHouse(this.destination.lng, this.destination.lat, this.destination.name)
    },

    // 在外部高德地图中打开当前目的地
    openExternalAmap() {
      if (!this.destination) return
      this.openAmapNavigation(this.destination.lng, this.destination.lat, this.destination.name)
    },

    // 搜索地址
    async searchLocation() {
      if (!this.searchAddress.trim()) {
        alert('请输入要查询的地址')
        return
      }

      try {
        // 使用高德地图地理编码API
        const geocoder = new this.AMap.Geocoder({
          city: '全国' // 限制城市，可选
        })

        geocoder.getLocation(this.searchAddress, (status, result) => {
          if (status === 'complete' && result.geocodes.length > 0) {
            const location = result.geocodes[0]
            this.showLocationOnMap(location)
          } else {
            alert('未找到该地址，请尝试更详细的地址信息')
          }
        })
        
      } catch (error) {
        console.error('地址搜索失败:', error)
        alert('地址搜索失败，请重试')
      }
    },

    // 在地图上显示位置
    showLocationOnMap(location) {
      // 清除之前的标记
      this.clearMarkers()
      
      const lnglat = [location.location.lng, location.location.lat]
      
      // 添加标记
      const marker = new this.AMap.Marker({
        position: lnglat,
        map: this.map,
        title: location.formattedAddress
      })
      
      this.markers.push(marker)
      
      // 设置地图中心
      this.map.setCenter(lnglat)
      this.map.setZoom(15)
      
      // 显示位置信息
      this.currentLocation = {
        address: location.formattedAddress,
        lng: location.location.lng.toFixed(6),
        lat: location.location.lat.toFixed(6)
      }
    },

    // 反向地理编码（点击地图获取地址）
    reverseGeocode(lnglat) {
      const geocoder = new this.AMap.Geocoder()
      
      geocoder.getAddress(lnglat, (status, result) => {
        if (status === 'complete' && result.regeocode) {
          this.showLocationOnMap({
            location: {
              lng: lnglat.lng,
              lat: lnglat.lat
            },
            formattedAddress: result.regeocode.formattedAddress
          })
        }
      })
    },

    // 获取用户位置
    getUserLocation() {
      if (!navigator.geolocation) {
        alert('您的浏览器不支持地理位置定位')
        return
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lng = position.coords.longitude
          const lat = position.coords.latitude
          this.userLocation = [lng, lat]
          
          // 反向地理编码获取地址
          this.reverseGeocode(new this.AMap.LngLat(lng, lat))
          
        },
        (error) => {
          console.error('定位失败:', error)
          let message = '定位失败'
          switch (error.code) {
            case error.PERMISSION_DENIED:
              message = '用户拒绝定位请求'
              break
            case error.POSITION_UNAVAILABLE:
              message = '位置信息不可用'
              break
            case error.TIMEOUT:
              message = '定位请求超时'
              break
          }
          alert(message)
        }
      )
    },

    // 清除所有标记
    clearMarkers() {
      this.markers.forEach(marker => {
        this.map.remove(marker)
      })
      this.markers = []
      // 保留 currentLocation，这样“目的地”信息不会因为重新规划路线而消失
    },

    // 添加收藏
    addBookmark() {
      if (!this.currentLocation) return
      
      this.bookmarks.push({
        address: this.currentLocation.address,
        lng: parseFloat(this.currentLocation.lng),
        lat: parseFloat(this.currentLocation.lat)
      })
      
      this.saveBookmarks()
      alert('位置已收藏')
    },

    // 移除收藏
    removeBookmark(index) {
      this.bookmarks.splice(index, 1)
      this.saveBookmarks()
    },

    // 缩放到收藏的位置
    zoomToBookmark(bookmark) {
      const lnglat = [bookmark.lng, bookmark.lat]
      
      // 清除之前的标记
      this.clearMarkers()
      
      // 添加标记
      const marker = new this.AMap.Marker({
        position: lnglat,
        map: this.map,
        title: bookmark.address
      })
      
      this.markers.push(marker)
      
      // 设置地图中心
      this.map.setCenter(lnglat)
      this.map.setZoom(15)
      
      // 显示位置信息
      this.currentLocation = {
        address: bookmark.address,
        lng: bookmark.lng.toFixed(6),
        lat: bookmark.lat.toFixed(6)
      }
    },

    // 保存收藏到本地存储
    saveBookmarks() {
      localStorage.setItem('mapBookmarks', JSON.stringify(this.bookmarks))
    },

    // 从本地存储加载收藏
    loadBookmarks() {
      const saved = localStorage.getItem('mapBookmarks')
      if (saved) {
        this.bookmarks = JSON.parse(saved)
      }
    }
  }
}
</script>

<style scoped>
.house-detail-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.back-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}

.back-btn:hover {
  background: #f5f5f5;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.sub-title {
  margin-left: auto;
  font-size: 13px;
  color: #909399;
}

.content {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 16px;
  padding: 16px;
  height: calc(100% - 56px);
  box-sizing: border-box;
}

.info-panel,
.map-panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 16px 18px;
  box-sizing: border-box;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  font-size: 13px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.address-item {
  grid-column: 1 / -1;
}

.label {
  color: #909399;
  font-size: 12px;
}

.value {
  color: #303133;
}

.value.highlight {
  font-size: 18px;
  font-weight: 600;
  color: #f56c6c;
}

.map-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.map-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid #409eff;
  background: #409eff;
  color: #fff;
  cursor: pointer;
}

.action-btn.secondary {
  border-color: #dcdfe6;
  background: #fff;
  color: #606266;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.map-container {
  position: relative;
  height: calc(100% - 8px);
}

.map {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.location-info {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(255, 255, 255, 0.96);
  padding: 10px 12px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  max-width: 280px;
  font-size: 12px;
  color: #303133;
}

.location-info h3 {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: #303133;
}

.location-info p {
  margin: 4px 0;
  line-height: 1.4;
  color: #303133;
}

.location-info strong {
  font-weight: 600;
  color: #303133;
}

@media (max-width: 960px) {
  .content {
    grid-template-columns: 1fr;
    height: auto;
  }

  .map-container {
    height: 360px;
  }
}
</style>