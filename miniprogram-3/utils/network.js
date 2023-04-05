var app = getApp()
//获取用户userToken
function getHeader(type) {
  // 判断登录token是否存在
  let contenttype = {
    'content-type': "application/json;charset=utf-8"
  }
  if (type == 'formdata') {
    contenttype = {
      'content-type': 'application/x-www-form-urlencoded;charset=utf-8'
    }
  }
  if (type == 'text') {
    contenttype = {
      "Content-Type": "application/text"
    }
  }
  if (wx.getStorageSync('userToken')) {
    // 获取token并设置请求头
    var token = wx.getStorageSync('userToken')
    let auth = {
      'authorization': 'Bearer ' + token.access_token,
      'content-type': "application/json;charset=utf-8"
    }
    if (type === 'formdata') {
      auth = {
        'authorization': 'Bearer ' + token.access_token,
        'content-type': 'application/x-www-form-urlencoded;charset=utf-8'
      }
    }
    if (type == 'text') {
      auth = {
        'authorization': 'Bearer ' + token.access_token,
        "Content-Type": "application/text"
      }
    }
    return auth
  } else {
    if (wx.getStorageSync('carts')) {
      var token = wx.getStorageSync('carts')
      let auth = {
        'Cookie': 'carts="' + token + '"',
        'content-type': "application/json;charset=utf-8"
      }
      if (type === 'formdata') {
        auth = {
          'Cookie': 'carts="' + token + '"',
          'content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
      }
      if (type === 'text') {
        auth = {
          'Cookie': 'carts="' + token + '"',
          "Content-Type": "application/text"
        }
      }
      return auth
    }
  }

  return contenttype
}

function refresh_token(method, url, param, type) {
  return new Promise((resolve, reject) => {
    let refresh = wx.getStorageSync('refresh_userToken')
    getrefresh(refresh.refresh_token).then(res => {
      let {
        code
      } = res
      if (code == "0") {
        settoken(res.data)
        httpRequest(method, url, param, type).then(res => {
          resolve(res)
        })
      } else {
        reject(res)
      }
    })
  })
}

function settoken(data) {
  wx.setStorage({
    key: "userToken",
    data: {
      access_token: data.access_token,
    }
  })
  wx.setStorage({
    key: "refresh_userToken",
    data: {
      refresh_token: data.refresh_token
    }
  })
}
//token 失效后 重新请求
function httpRequest(method, url, param, type) {
  let _this = this;
  let requestheader = getHeader()
  if (type == 1) {
    requestheader = getHeader('formdata')
  }
  wx.showLoading({
    title: '请求中，请耐心等待...',
  });
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: param,
      method: method,
      header: requestheader,
      success: res => {
        setTimeout(function () {
          wx.hideLoading()
        }, 500)
        resolve(res.data);
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
// 获取 token
function getrefresh(refresh_token) {
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiUrl}/api/verifycations/refresh/token/`,
      data: {
        refresh_token
      },
      method: 'post', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader(),
      success: res => {
        resolve(res.data);
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
//get请求
function get(url, data = {}) {
  let haderType = getHeader()
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: data,
      method: 'GET', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: haderType,
      success: res => {
        let {
          code
        } = res.data
        if (code == '401') {
          refresh_token('get', url, data, 0).then(res => {
            resolve(res);
          })
        } else {
          resolve(res.data);
        }
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
//post请求
function post(url, data = {}) {
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: data,
      method: 'POST', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader(),
      success: res => {
        let {
          code
        } = res.data
        if (code == '401') {
          //method,url,data={},type
          refresh_token('post', url, data, 0).then(res => {
            resolve(res);
          })
        } else {
          resolve(res.data);
        }

      },
      fail: err => {
        reject(err)
      }
    })
  });
}

function postFormData(url, data = {}) {
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: data,
      method: 'POST', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader('formdata'),
      success: res => {
        let {
          code
        } = res.data
        if (code == '401') {
          //method,url,data={},type
          refresh_token('post', url, data, 1).then(res => {
            resolve(res);
          })
        } else {
          resolve(res.data);
        }
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
//PUT请求
function put(url, data = {}) {
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: data,
      method: 'PUT', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader(),
      success: res => {
        let {
          code
        } = res.data
        if (code == '401') {
          //method,url,data={},type
          refresh_token('post', url, data, 1).then(res => {
            resolve(res);
          })
        } else {
          resolve(res.data);
        }
      },
      fail: err => {
        reject(err)
      }
    })
  });
}

//DELETE请求
function remove(url, data = {}) {
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: url,
      data: data,
      method: 'DELETE', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader('formdata'),
      success: res => {
        resolve(res.data);
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
//参数转换
function convertObj(data) {
  let _result = [];
  for (let key in data) {
    let value = data[key];
    if (value.constructor == Array) {
      value.forEach(function (_value) {
        _result.push(key + "=" + _value);
      });
    } else {
      _result.push(key + '=' + value);
    }
  }
  return _result.join('&');
}
//传参DELETE请求
function deletes(url, data = {}) {
  let urls = url + '?' + convertObj(data)
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: urls,
      method: 'DELETE', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader(),
      success: res => {
        resolve(res.data);
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
//传参DELETE请求
function deletesdataurl(url, data = {}) {
  let urls = url + '?' + convertObj(data)
  let _this = this;
  return new Promise((resolve, reject) => {
    wx.request({
      url: urls,
      method: 'DELETE', // OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
      header: getHeader(),
      success: res => {
        let {
          code
        } = res.data
        if (code == '401') {
          //method,url,data={},type
          refresh_token('post', url, data, 1).then(res => {
            resolve(res);
          })
        } else {
          resolve(res.data);
        }
      },
      fail: err => {
        reject(err)
      }
    })
  });
}
module.exports = {
  get,
  post,
  postFormData,
  deletesdataurl,
  put,
  remove,
  deletes
}