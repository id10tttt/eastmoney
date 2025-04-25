// pages/vip-detail/vip-detail.js
import stock_api from '../../api/stock.js'
import Message from 'tdesign-miniprogram/message/index';
import * as echarts from '../../ec-canvas/echarts';
var option = []; //图表配置项 声明
// 初始化图表函数  开始
let chart2 = null;

function initChart2(canvas, width, height, dpr) {
  chart2 = echarts.init(canvas, null, {
    width: width,
    height: height,
    devicePixelRatio: dpr
  })
  canvas.setChart(chart2)
  return chart2;
}
Page({

  /**
   * 页面的初始数据
   */
  data: {
    rain_image: '/static/yin@2x.png',
    sun_image: '/static/yang@2x.png',
    danger_image: '/static/lei@2x.png',
    stock_code: '',
    stock_name: '',
    vip_content: [],
    current_collapse: 0,
    benchmark_count: {},
    ec2: {
      onInit: initChart2
    },
  },
  syncVIPContent(type_id) {
    let that = this
    let payload_data = {
      header: {
      },
      body: {
        stock_code: this.data.stock_code,
        type_id: type_id
      }
    }
    stock_api.sync_stock_vip_content(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {

      } else {

      }
    })
  },
  handlehangeCollapse(e) {
    let current_collapse = e.detail.value
    let id = e.currentTarget.dataset.ids
    let types = e.currentTarget.dataset.compare_type;
    if(current_collapse.length!=0&&types=="vs"){
      this.data.vip_content.forEach(res=>{
        if(res.benchmark_id==current_collapse[0]){
          this.initEchartView(res.value,res.benchmark_id);
        }
      })
    }else{
      if(types=="vs"){
        let cartId = '#mychart-dom-bar-'+id
        this.ecComponent = this.selectComponent(cartId);
        this.ecComponent.chart.clear();
      }
    }
  },
  fetchStockVIPContetnt() {
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        stock_code: this.data.stock_code
      }
    }
    wx.showLoading({
      title: '加载中...',
    })
    stock_api.fetch_stock_vip_content(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        wx.hideLoading({
          success: (res) => {},
        })
        that.setData({
          vip_content: result.data.data,
          stock_code: result.data.stock_code,
          stock_name: result.data.stock_name,
          benchmark_count: result.data.benchmark_count
        })
      } else {  
      wx.navigateTo({
          url: '/pages/subscribe/subscribe?stock_code='+that.data.stock_code,
      });
      }
    })
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    // var stock_code = JSON.parse(options.stock)
    // this.setData({
    //   stock_code: stock_code.stock_code
    // })
  },
  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    let pages = getCurrentPages();
    let currentPage = pages[pages.length-1];
    console.log(currentPage.options);
    var stock_code = JSON.parse(currentPage.options.stock)
    this.setData({
      stock_code: stock_code.stock_code
    })
    this.fetchStockVIPContetnt()
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {

  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {

  },
  getEchartsOption(detail_data){
    let option = {}
    let date_value = Array()
    let date_data_value = Array()
    if (detail_data) {
      detail_data.map(res => {
        if(res[0]){
          date_value.push(res[1])
          date_data_value.push(res[0].toFixed(2))
        }
      })
      option = {
        xAxis: {
          type: 'category',
          data: date_value,
          boundaryGap: false,
          axisLabel: {
            show: true,
            interval: 0,
            rotate: 45
          }
        },
        grid: {
          containLabel: true
        },
        tooltip: {
          show: true,
          trigger: 'axis',
          axisPointer: {
            type: 'line'
          }
        },
        toolbox: {
          show: true,
          feature: {
            magicType: {
              show: true,
              type: ["line", "bar"]
            },
            saveAsImage: {
              show: false
            },
          }
        },
        yAxis: {
          x: 'center',
          type: 'value',
          splitLine: {
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        series: [{
            label: { //数据显示
              show: true,
              color: 'inherit',
              position: 'top',
              fontSize: 10,
            },
            data: date_data_value,
            type: 'line'
          }
        ]
      }
    }
    return option
  },
  initEchartView(datas,id) {
    let cartId = '#mychart-dom-bar-'+id
    this.ecComponent = this.selectComponent(cartId);
    this.ecComponent.init((canvas, width, height, dpr) => {
      // 获取组件的 canvas、width、height 后的回调函数
      // 在这里初始化图表
      const chart = echarts.init(canvas, null, {
        width: width,
        height: height,
        devicePixelRatio: dpr // new
      });
      console.log('start refresh...')
      let option = this.getEchartsOption(datas)
      chart.setOption(option, true);
      // 将图表实例绑定到 this 上，可以在其他成员函数（如 dispose）中访问
      this.chart = chart;
      // 注意这里一定要返回 chart 实例，否则会影响事件处理等
      return chart;
    });
  },
 
})