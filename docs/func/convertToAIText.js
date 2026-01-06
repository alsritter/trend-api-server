// 在这里，您可以通过 'params'  获取节点中的输入变量，并通过 'ret' 输出结果
// 'params' 已经被正确地注入到环境中
// 下面是一个示例，获取节点输入中参数名为'input'的值：
// const input = params.input; 
// 下面是一个示例，输出一个包含多种数据类型的 'ret' 对象：
// const ret = { "name": '小明', "hobbies": ["看书", "旅游"] };

async function main({ params }: Args): Promise<Output> {
    const platformData = params.platformData;
    const includeComments = params.includeComments !== false; // 默认 true
    const maxCommentsPerContent = params.maxCommentsPerContent || 10;
    const maxContents = params.maxContents || 10; // 默认最多输出 10 个帖子

    // 平台映射
    const platformMap = {
        "xhs": "小红书",
        "dy": "抖音",
        "ks": "快手",
        "bili": "哔哩哔哩",
        "wb": "微博",
        "tieba": "百度贴吧",
        "zhihu": "知乎"
    };

    const contentTextArray = [];
    let totalContents = 0;
    let totalComments = 0;

    // 计算每个平台应该分配的内容数量
    let totalProcessedContents = 0;

    // 遍历每个平台
    platformData.forEach((platform, platformIndex) => {
        totalContents += platform.total_contents;
        totalComments += platform.total_comments;

        // 如果已经达到最大内容数，跳过后续平台
        if (totalProcessedContents >= maxContents) {
            return;
        }

        // 计算当前平台可以显示的内容数量
        const maxAllowed = Math.min(
            maxContents - totalProcessedContents,
            platform.contents.length
        );

        // 限制每个平台的内容数量
        const contentsToShow = platform.contents.slice(0, maxAllowed);
        totalProcessedContents += contentsToShow.length;

        // 遍历每个内容
        contentsToShow.forEach((content, contentIndex) => {
            let contentText = '';
            
            // 平台和基本信息
            const platformName = platformMap[platform.platform] || platform.platform;
            contentText += `平台: ${platformName}\n`;
            contentText += `标题: ${content.title || '无标题'}\n`;
            contentText += `类型: ${content.type}\n`;
            
            if (content.ip_location) {
                contentText += `地区: ${content.ip_location}\n`;
            }
            
            // 内容描述
            if (content.desc) {
                contentText += `\n内容描述:\n${content.desc}\n`;
            }
            
            // 互动数据
            contentText += `\n互动数据:\n`;
            contentText += `  点赞: ${content.liked_count || 0}\n`;
            contentText += `  收藏: ${content.collected_count || 0}\n`;
            contentText += `  评论: ${content.comment_count || 0}\n`;
            contentText += `  分享: ${content.share_count || 0}\n`;
            
            // 标签
            if (content.tag_list) {
                try {
                    const tags = JSON.parse(content.tag_list);
                    if (Array.isArray(tags) && tags.length > 0) {
                        contentText += `标签: ${tags.join(', ')}\n`;
                    }
                } catch (e) {
                    if (content.tag_list) {
                        contentText += `标签: ${content.tag_list}\n`;
                    }
                }
            }
            
            // 发布时间
            if (content.time) {
                const publishTime = new Date(content.time).toLocaleString('zh-CN');
                contentText += `发布时间: ${publishTime}\n`;
            }
            
            // 来源关键词
            if (content.source_keyword) {
                contentText += `来源关键词: ${content.source_keyword}\n`;
            }
            
            // 评论
            if (includeComments && content.comments && content.comments.length > 0) {
                const commentsToShow = content.comments.slice(0, maxCommentsPerContent);
                contentText += `\n评论 (显示前 ${commentsToShow.length} 条):\n`;
                
                commentsToShow.forEach((comment, commentIndex) => {
                    contentText += `  [${commentIndex + 1}]`;
                    if (comment.ip_location) {
                        contentText += ` (${comment.ip_location})`;
                    }
                    contentText += `:\n`;
                    contentText += `      ${comment.content}\n`;
                    if (comment.like_count && parseInt(comment.like_count) > 0) {
                        contentText += `      点赞: ${comment.like_count}\n`;
                    }
                    if (comment.sub_comment_count && parseInt(comment.sub_comment_count) > 0) {
                        contentText += `      回复数: ${comment.sub_comment_count}\n`;
                    }
                });
                
                if (content.comments.length > maxCommentsPerContent) {
                    contentText += `  ... 还有 ${content.comments.length - maxCommentsPerContent} 条评论未显示\n`;
                }
            }
            
            contentTextArray.push(contentText);
        });
    });

    // 构建返回对象
    const ret = {
        contentTextArray: contentTextArray,
        mergedText: contentTextArray.join('\n=============\n')
    };

    return ret;
}