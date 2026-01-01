import { Args } from '@/runtime';
import { Input, Output } from "@/typings/triggerCrawlForHotspot/triggerCrawlForHotspot";
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
    const baseUrl = 'https://bizradarapi.xingsuancn.com';

    const requestData = {
      hotspot_id: Number(input.hotspotId),
      platforms: input.platforms || ['xhs', 'dy', 'bili'],
      crawler_type: input.crawlerType || 'search',
      max_notes_count: Number(input.maxNotesCount) || 20,
      enable_comments: true,
      enable_sub_comments: false,
      max_comments_count: Number(input.maxCommentsCount) || 20,
    };

    logger.info('触发爬虫任务', { baseUrl, requestData });

    const response = await axios.post(
      `${baseUrl}/api/v1/hotspots/trigger-crawl`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 30000
      }
    );

    logger.info('爬虫任务创建成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: response.data.message || '爬虫任务创建成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('触发爬虫任务失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `触发爬虫任务失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};