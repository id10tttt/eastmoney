company_data = {
  "jbzl": {
    "gsmc": "江苏鱼跃医疗设备股份有限公司",
    "ywmc": "Jiangsu Yuyue Medical Equipment and Supply Co., Ltd.",
    "cym": "--",
    "agdm": "002223",
    "agjc": "鱼跃医疗",
    "bgdm": "--",
    "bgjc": "--",
    "hgdm": "--",
    "hgjc": "--",
    "zqlb": "深交所主板A股",
    "sshy": "医疗行业",
    "ssjys": "深圳证券交易所",
    "sszjhhy": "制造业-专用设备制造业",
    "zjl": "吴群",
    "frdb": "吴群",
    "dm": "王瑞洁",
    "dsz": "吴群",
    "zqswdb": "张雨阳",
    "dlds": "万遂人,王千华,于春",
    "lxdh": "0511-86900802",
    "dzxx": "dongmi@yuyue.com.cn",
    "cz": "0511-86900876",
    "gswz": "www.yuyue.com.cn",
    "bgdz": "江苏丹阳市云阳工业园(振新路南)",
    "zcdz": "江苏省丹阳市云阳工业园(振新路南)",
    "qy": "江苏",
    "yzbm": "212300",
    "zczb": "10.02亿",
    "gsdj": "91321100703952657W",
    "gyrs": "5525",
    "glryrs": "25",
    "lssws": "上海市通力律师事务所",
    "kjssws": "信永中和会计师事务所(特殊普通合伙)",
    "gsjj": "    江苏鱼跃医疗设备股份有限公司自1998年创立以来,矢志于投身生命健康事业,实业与资本双轮驱动、国际资源与本土动力兼具、医疗市场与家用市场共进、产品与服务模式双重融合,组建了一个覆盖医疗器械领域的专业化服务平台。集团旗下拥有1家上市公司,鱼跃医疗(SZ:002223),及80余家参控股公司。经过多年的发展,鱼跃集团旗下目前拥有包括鱼跃医疗、意大利百胜等著名品牌。集团总部设立在中国上海,拥有位于德国、意大利、北京等10大研发中心和7大制造中心,并在全球各地设立了56家办事机构,形成了完整的研发、生产、营销和服务网络。把全球各地人民的健康需求和专业的理念融入持续的创新,为生命健康保驾护航。回望来路,鱼跃经历了两个十年:1998-2008,第一个十年,为了生存而奋斗,Liveforsurvive;2008-2018,第二个十年,为了生活而奋斗;Liveforlife;而未来的十年,2018-2028,鱼跃将肩负更大的使命,为更多健康的生命而奋斗,Liveforlives。我们将持续秉承健康立心,科技立行,满怀热忱与希望,守护企业、社会与人们共生共荣的健康节奏,让科技律动生命!",
    "jyfw": "医疗器械(按许可证所核范围经营);保健用品的制造与销售;金属材料的销售;经营本企业自产产品的出口业务和本企业所需的机械设备、零配件、原辅材料的进口业务(国家限定公司经营或禁止进出口的商品及技术除外);机动医疗车改装(凭相关资质开展经营活动);汽车的销售;消毒剂销售(不含危险化学品);个人卫生用品销售;卫生用品和一次性使用医疗用品生产;食品经营。(依法须经批准的项目,经相关部门批准后方可开展经营活动)"
  },
  "fxxg": {
    "clrq": "1998-10-22",
    "ssrq": "2008-04-18",
    "fxsyl": "29.08",
    "wsfxrq": "2008-04-08",
    "fxfs": "网下询价配售",
    "mgmz": "1.00",
    "fxl": "2600万",
    "mgfxj": "9.48",
    "fxfy": "1922万",
    "fxzsz": "2.465亿",
    "mjzjje": "2.273亿",
    "srkpj": "16.50",
    "srspj": "14.30",
    "srhsl": "74.46%",
    "srzgj": "16.80",
    "wxpszql": "0.37%",
    "djzql": "0.08%"
  },
  "Code": "SZ002223",
  "CodeType": "ABStock",
  "SecuCode": "002223.SZ",
  "SecurityCode": "002223",
  "SecurityShortName": "鱼跃医疗",
  "MarketCode": "02",
  "Market": "SZ",
  "SecurityType": None,
  "ExpireTime": "/Date(-62135596800000)/"
}

def parse_east_money_company_data(company_data):
    basic_info = company_data.get('jbzl', {})
    parse_data = {
        'name': basic_info.get('gsmc'),
        'name_en': basic_info.get('ywmc'),
        'name_old': basic_info.get('cym'),
        'code_a': basic_info.get('agdm'),
        'code_a_desc': basic_info.get('agjc'),
        'code_b': basic_info.get('bgdm'),
        'code_b_desc': basic_info.get('bgjc'),
        'code_h': basic_info.get('hgdm'),
        'code_h_desc': basic_info.get('hgjc'),
        'bond_type': basic_info.get('zqlb'),
        'belong_east_type': basic_info.get('sshy'),
        'listing_exchange': basic_info.get('ssjys'),
        'belong_src_industry': basic_info.get('sszjhhy'),
        'ceo': basic_info.get('zjl'),
        'legal_name': basic_info.get('frdb'),
        'chairman_secretary': basic_info.get('dm'),
        'chairman': basic_info.get('dsz'),
        'securities_affairs_representative': basic_info.get('zqswdb'),
        'independent_director': basic_info.get('dlds'),
        'phone': basic_info.get('lxdh'),
        'email': basic_info.get('dzxx'),
        'fax': basic_info.get('cz'),
        'website': basic_info.get('gswz'),
        'office_address': basic_info.get('bgdz'),
        'regist_address': basic_info.get('zcdz'),
        'province': basic_info.get('qy'),
        'zip': basic_info.get('yzbm'),
        'regist_capital': basic_info.get('zczb'),
        'credit_code': basic_info.get('gsdj'),
        'employee_count': basic_info.get('gyrs'),
        'manager_count': basic_info.get('glryrs'),
        'law_office': basic_info.get('lssws'),
        'account_firm': basic_info.get('kjssws'),
        'company_introduction': basic_info.get('gsjj'),
        'bussiness_scope': basic_info.get('jyfw'),
    }
    return parse_data