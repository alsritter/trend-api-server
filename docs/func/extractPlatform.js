// 在这里，您可以通过 'params' 获取节点中的输入变量，并通过 'ret' 输出结果
// 'params' 已经被正确地注入到环境中
// 
// 输入参数说明：
// params.hotspotData - 单个热点数据对象
//
// 输出说明：
// 返回: { platform, platform_info }
// platform - 平台名称 (如: "哔哩哔哩")
// platform_info - 平台详细信息对象 (包含 platform, rank, seen_at, heat_score)

async function main({ params }) {
    const hotspotData = params.hotspotData;

    // 中文平台名称到英文key的映射
    const platformMap = {
        "小红书": "xhs",
        "抖音": "dy",
        "哔哩哔哩": "bili",
        "快手": "ks",
        "微博": "wb",
        "贴吧": "tieba",
        "知乎": "zhihu"
    };

    // 检查数据有效性
    if (!hotspotData || !hotspotData.platforms || hotspotData.platforms.length === 0) {
        return {
            platform: null
        };
    }

    // 提取第一个平台信息
    const firstPlatform = hotspotData.platforms[0];
    const chineseName = firstPlatform.platform;
    
    // 转换为英文key，如果找不到映射则使用原值
    const englishKey = platformMap[chineseName] || chineseName;
    
    const ret = {
        platform: englishKey
    };

    return ret;
}

// 使用示例：
// const result = await main({ 
//   params: {
//     hotspotData: {
//       id: 721,
//       keyword: ""十年之约"",
//       platforms: [
//         { platform: "哔哩哔哩", rank: 0, seen_at: "2026-01-01", heat_score: 339017 }
//       ]
//     }
//   }
// });
// 
// 返回结果:
// {
//   platform: "哔哩哔哩",
//   platform_info: {
//     platform: "哔哩哔哩",
//     rank: 0,
//     seen_at: "2026-01-01",
//     heat_score: 339017
//   }
// }
