import request from './request'

export function getDistricts() {
  return request.get('/prediction/districts/')
}

export function predictPrice(payload: Record<string, any>) {
  return request.post('/prediction/predict/', payload)
}

export function getModelStatus() {
  return request.get('/prediction/status/')
}
