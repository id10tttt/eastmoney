import {post} from '../utils/network.js'
const app = getApp()

function check_user_vip(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/vip/check`,data);
}

module.exports = {
  check_user_vip
}