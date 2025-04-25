// index.js
import Toast from 'tdesign-miniprogram/toast/index';
import stock_api from '../../api/stock.js'
import query_api from '../../api/query_his'
import user_api from '../../api/user.js'

const app = getApp()

Page({
  /**
   * 页面的初始数据
   */
  data: {
    query_his: [],
    stock_code: '',
    user_name: '我',
    cur: {
      value: 'bottom',
      text: '交易很多次，总有亏有赚，但年底总账的亏损是因为有“大亏”的操作。Pick Best使用市场大数据，帮您避免买入可能带来“大亏”的公司。'
    },
    visible: false,
    isShowClear: false,
    showInputStatus: false,
    bindSource: [],
    clear_icon: '../../static/clear.png'
  },

  clearInput: function (e) {
    this.setData({
      stock_code: "",
      isShowClear: false,
      showInputStatus: false
    })
  },
  query_finance_stock(query_word){
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        query: query_word
      }
    }
    stock_api.query_finance_stock(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){
        that.setData({
          bindSource: result.data,
          showInputStatus: true
        })
      }
    })
  },
  stockCode(e) {
    let query_word = e.detail.value
    if(query_word){
      this.setData({
        stock_code: e.detail.value
      })
      this.query_finance_stock(e.detail.value)
    }
    else{
      this.setData({
        showInputStatus: false
      })
    }
  },
  clearStockCode(e) {
    this.setData({
      stock_code: "",
      showInputStatus: false
    })
  },
  fetch_finance_stock_list() {
    let that = this
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    stock_api.fetch_finance_stock(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {

      } else {

      }
    })
  },
  //点击搜索
  searchOne() {
    this.onClickSearch()
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {

  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  fetchQueryHis() {
    let that = this
    let payload_data = {
      body: {

      }
    }
    query_api.query_his(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        that.setData({
          query_his: result.data.data
        })
      }
    })
  },

  getMyProfile() {
    let that = this
    let payload_data = {

    }
    user_api.get_my_profile(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        let avatar_url = result.data.avatar_url
        if (!avatar_url) {
          avatar_url = defaultAvatarUrl
        }
        that.setData({
          user_name: result.data.nickname,
        })
      }
    })
  },
  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    this.fetchQueryHis()
    this.getMyProfile()
  },
  handleCloseTag(e) {
    console.log('sdsdsdsd', e)
    let stock_code = e.target.dataset.value
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        key: stock_code
      }
    }
    query_api.unlink_query_his(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        that.fetchQueryHis()
      }
    })
  },
  onClickOpenPage(e) {
    let stock_code = e.target.dataset.value
    this.setData({
      stock_code: stock_code,
      isShowClear: true
    })
    this.onClickSearch()
  },

  onClickSearch() {
    let that = this;

    if (that.data.stock_code) {
      wx.showLoading({
        title: '加载中...',
      })
      var payload_data = {
        "header": {},
        body: {
          stock_code: that.data.stock_code
        }
      }
      stock_api.validate_stock(payload_data).then(res => {
        var result = res.result;
        var code = result.code;
        if (code == 200) {
          if (result.data.code) {
            wx.hideLoading();
            var stock_data = {
              stock_code: that.data.stock_code
            }
            wx.navigateTo({
              url: '/pages/detail/detail?stock=' + JSON.stringify(stock_data),
            });
          } else {
            Toast({
              context: that,
              selector: '#t-toast',
              message: '股票: ' + that.data.value + ', 不存在或异常',
            });
          }
        } else {
          Toast({
            context: this,
            selector: '#t-toast',
            message: result.data,
          });
        }
      })
      wx.hideLoading()
    } else {
      Toast({
        context: this,
        selector: '#t-toast',
        message: '请先输入股票代码',
        theme: 'warning',
        direction: 'column'
      });
    }
  },
  setSearchValue(e) {
    this.setData({
      stock_code: e.detail.value
    })
  },
  handlePopup(e) {
    this.setData({
      visible: true
    });
  },
  onVisibleChange(e) {
    this.setData({
      visible: e.detail.visible,
    });
  },
  handleMyProfile() {
    wx.navigateTo({
      url: '/pages/my/my'
    });
  },
  itemtap(e){
    let current_code = e.target.dataset.name
    this.setData({
      stock_code: current_code,
      showInputStatus: false,
      bindSource: []
    })

  }
})
