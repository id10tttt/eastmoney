import {post} from '../utils/network.js'
const app = getApp()

function get_subscribe_list(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/pay/subscribe/list`,data);
}

function subscribe_item(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/pay/subscribe`,data);
}

module.exports = {
  get_subscribe_list,
  subscribe_item
}