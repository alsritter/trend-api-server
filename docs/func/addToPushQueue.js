import { Args } from '@/runtime';
import { Input, Output } from "@/typings/addToPushQueue/addToPushQueue";
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
      report_id: Number(input.reportId),
      channels: input.channels || ['wechat', 'email']
    };

    logger.info('添加到推送队列', { baseUrl, requestData });

    const response = await axios.post(
      `${baseUrl}/api/v1/hotspots/push-queue`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      }
    );

    logger.info('添加到推送队列成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: response.data.message || '成功添加到推送队列',
      data: response.data
    };

  } catch (error: any) {
    logger.error('添加到推送队列失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `添加到推送队列失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};
