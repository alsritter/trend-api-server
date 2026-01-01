import { Args } from '@/runtime';
import { Input, Output } from "@/typings/listHotspots/listHotspots";
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

    const params: any = {
      page: Number(input.page) || 1,
      page_size: Number(input.pageSize) || 20
    };

    if (input.status) {
      params.status = input.status;
    }
    if (input.keyword) {
      params.keyword = input.keyword;
    }
    if (input.similaritySearch) {
      params.similarity_search = input.similaritySearch;
    }
    if (input.similarityThreshold !== undefined) {
      params.similarity_threshold = Number(input.similarityThreshold);
    }

    logger.info('获取热点列表', { baseUrl, params });

    const response = await axios.get(
      `${baseUrl}/api/v1/hotspots/list`,
      {
        params,
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 15000
      }
    );

    logger.info('获取热点列表成功', { status: response.status, data: response.data });

    return {
      success: true,
      message: '获取热点列表成功',
      data: response.data
    };

  } catch (error: any) {
    logger.error('获取热点列表失败', {
      error: error.message,
      response: JSON.stringify(error)
    });

    return {
      success: false,
      message: `获取热点列表失败: ${error.message}`,
      error: error.response?.data || error.message
    };
  }
};
