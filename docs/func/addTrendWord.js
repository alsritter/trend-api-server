import { Args } from '@/runtime';  
import { Input, Output } from "@/typings/addTrendWord/addTrendWord";  
import axios from 'axios';  

/**  
 * Each file needs to export a function named `handler`. This function is the entrance to the Tool.  
 * @param {Object} args.input - input parameters, you can get test input value by input.xxx.  
 * @param {Object} args.logger - logger instance used to print logs, injected by runtime  
 * @returns {*} The return data of the function, which should match the declared output parameters.  
 *   
 * Remember to fill in input/output in Metadata, it helps LLM to recognize and use tool.  
 */  
export async function handler({ input, logger }: Args<Input>): Promise<Output> {  
  try {
    // 设置基础 URL (根据环境可以调整)
    const baseUrl = 'https://bizradarapi.xingsuancn.com';
    
    // 构建请求数据
    const requestData = {
      analysis: {
        title: input.title,
        confidence: Number(input.confidence) || 0.9,
        primaryCategory: input.primaryCategory || '待研究',
        tags: input.tags || [],
        reasoning: {
          keep: input.reasoningKeep || [],
          risk: input.reasoningRisk || []
        },
        opportunities: input.opportunities || [],
        isRemove: input.isRemove || false
      },
      platform_data: {
        date: input.date,
        icon: input.icon || '',
        name: input.name,
        rank: Number(input.rank),
        type: input.platformType,
        url: input.url,
        viewnum: input.viewnum,
        word_cover: {
          uri: input.wordCoverUri || '',
          url_list: input.wordCoverUrlList || []
        },
        word_type: input.wordType || '无'
      }
    };

    logger.info('发送添加热词请求', { baseUrl, requestData });

    // 发起 POST 请求
    const response = await axios.post(
      `${baseUrl}/api/v1/hotspots/add-keyword`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000 // 10秒超时
      }
    );

    logger.info('请求成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: '热词添加成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('添加热词失败', { 
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `添加热词失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};