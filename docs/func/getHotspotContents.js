import { Args } from '@/runtime';
import { Input, Output } from "@/typings/getHotspotContents/getHotspotContents";
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
    const hotspotId = Number(input.hotspotId);

    logger.info('获取热点内容', { baseUrl, hotspotId });

    const response = await axios.get(
      `${baseUrl}/api/v1/hotspots/${hotspotId}/contents`,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 30000
      }
    );

    logger.info('获取热点内容成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: '获取热点内容成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('获取热点内容失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `获取热点内容失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};