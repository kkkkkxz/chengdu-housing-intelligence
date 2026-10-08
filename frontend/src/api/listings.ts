import request from './/request'
import { authApi } from './auth'

export interface HouseQuery {
    page: number,
    page_size: number,
    search: string,
    rooms: undefined,
    price_min: undefined,
    halls: undefined,
    ordering?: string
}
export const listingsApi = {
  getHouses(params: HouseQuery) {
    return request.get('/listings/houses/', { params })
  },
  getHouseDetail(id: number) {
    return request.get(`/listings/houses/${id}/`)
  },
  favorite(id: number) {
    return request.post(`/listings/houses/${id}/favorite/`)
  },
  unfavorite(id: number) {
    return request.delete(`/listings/houses/${id}/unfavorite/`)
  },
  myFavorites(params?: Record<string, any>) {
    return request.get('/listings/favorites/', { params })
  },
  getSimilarHouses(id: number) {
    return request.get(`/listings/houses/${id}/similar/`)
  },
  getRecommendations() {
  return request.get('/listings/houses/recommendations/')
  },
  getSummary(params?: Record<string, any>) {
    return request.get('/listings/houses/summary/', { params })
  },

  // stats
  statsAvgPriceByDistrict(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/average-price-by-district/', {params})
  },
  statsPriceRange(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/price-range/', {params})
  },
  statsHouseTypeCount(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/house-type-count/', {params})
  },
  statsAvgPriceByBuildingType(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/avg-price-by-building-type/', {params})
  },
  statsPriceAreaScatter(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/price-area-scatter/', {params})
  },
  statsTitleWordcloud(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/title-wordcloud/', {params})
  },
  statsDistrictMapCount(params?: Record<string, any>) {
    return request.get('/listings/houses/stats/district-map-count/', {params})
  },


}