import {
  post
} from '../utils/network.js'
const app = getApp()

function login_user(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/program/login`, data);
}

function bind_user(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/program/bind`, data);
}

function check_token(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/token/check`, data);
}

function api_login(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/user/auth`, data);
}

module.exports = {
  login_user,
  bind_user,
  check_token,
  api_login
}