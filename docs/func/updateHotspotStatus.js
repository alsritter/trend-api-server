import { Args } from '@/runtime';
import { Input, Output } from "@/typings/updateHotspotStatus/updateHotspotStatus";
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

    const requestData = {
      status: input.status
    };

    logger.info('更新热点状态', { baseUrl, hotspotId, requestData });

    const response = await axios.patch(
      `${baseUrl}/api/v1/hotspots/${hotspotId}/status`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      }
    );

    logger.info('更新热点状态成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: response.data.message || '更新热点状态成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('更新热点状态失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `更新热点状态失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};
