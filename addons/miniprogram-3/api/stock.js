import {post} from '../utils/network.js'
var app = getApp()

function fetch_finance_exchange(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/finance/stock/exchange`, data)
}

function fetch_finance_stock(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/finance/stock/list`, data)
}

function query_finance_stock(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/finance/stock/query`, data)
}

function validate_stock(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/stock/validate`, data)
}

function list_mine_stock(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/sweep/list`, data)
}

function fetch_stock_free_value(data){
  return post(`${app.globalData.apiUrl}/v1/api/wechat/mini/sweep/value/free`, data)
}

function fetch_stock_vip_content(data){
  return post(`${app.globalData.apiUrl}/v1/api/wechat/mini/vip/content`, data)
}

function fetch_stock_vip_content_detail(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/vip/content/detail`, data)
}

function sync_stock_vip_content(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/vip/content/sync`, data)
}

module.exports = {
  validate_stock,
  list_mine_stock,
  fetch_stock_free_value,
  fetch_finance_stock,
  fetch_finance_exchange,
  fetch_stock_vip_content,
  fetch_stock_vip_content_detail,
  sync_stock_vip_content,
  query_finance_stock
}