import { Args } from '@/runtime';
import { Input, Output } from "@/typings/addBusinessReport/addBusinessReport";
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
      report: input.report,
      score: Number(input.score) || 0,
      priority: input.priority || 'medium',
      product_types: input.productTypes || []
    };

    logger.info('添加商业报告', { baseUrl, requestData });

    const response = await axios.post(
      `${baseUrl}/api/v1/hotspots/business-report`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 15000
      }
    );

    logger.info('添加商业报告成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: response.data.message || '商业报告添加成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('添加商业报告失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `添加商业报告失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};
