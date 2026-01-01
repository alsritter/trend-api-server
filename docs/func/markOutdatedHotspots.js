import { Args } from '@/runtime';
import { Input, Output } from "@/typings/markOutdatedHotspots/markOutdatedHotspots";
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
    const days = Number(input.days) || 2;

    logger.info('标记过时热点', { baseUrl, days });

    const response = await axios.post(
      `${baseUrl}/api/v1/hotspots/mark-outdated`,
      null,
      {
        params: { days },
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 15000
      }
    );

    logger.info('标记过时热点成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: response.data.message || '标记过时热点成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('标记过时热点失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `标记过时热点失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};
