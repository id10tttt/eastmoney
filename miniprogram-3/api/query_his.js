import {
  post
} from '../utils/network.js'
const app = getApp()

function query_his(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/query/his/list`, data);
}

function unlink_query_his(data) {
  return post(`${app.globalData.apiUrl}/api/wechat/mini/query/his/unlink`, data);
}

module.exports = {
  query_his,
  unlink_query_his
}