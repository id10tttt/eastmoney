import {post} from '../utils/network.js'
const app = getApp()

function check_user_vip(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/vip/check`,data);
}

function get_my_profile(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/program/profile`,data);
}

function update_my_profile(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/program/profile/update`,data);
}

function add_collect(data){
  return post(`${app.globalData.apiUrl}/api/wechat/mini/my/collect/add`,data);
}
module.exports = {
  check_user_vip,
  add_collect,
  get_my_profile,
  update_my_profile
}