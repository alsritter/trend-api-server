import {
  Card,
  Table,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  message,
  Divider
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tasksApi } from "@/api/tasks";
import {
  PLATFORM_OPTIONS,
  CRAWLER_TYPE_OPTIONS,
  TASK_STATUS_MAP
} from "@/utils/constants";
import { formatDateTime } from "@/utils/format";
import { useState } from "react";
import type { TaskCreateRequest } from "@/types/api";

function Tasks() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [selectedCrawlerType, setSelectedCrawlerType] = useState<string>("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // 查询任务列表
  const { data: tasksData, isLoading } = useQuery({
    queryKey: ["tasks", currentPage, pageSize],
    queryFn: () => tasksApi.list({ page: currentPage, page_size: pageSize }),
    refetchInterval: 5000 // 每5秒自动刷新
  });

  // 创建任务
  const createMutation = useMutation({
    mutationFn: tasksApi.create,
    onSuccess: (data) => {
      message.success(`任务创建成功！任务ID: ${data.task_id}`);
      setIsModalOpen(false);
      form.resetFields();
      // 刷新任务列表
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    }
  });

  // 停止任务
  const stopMutation = useMutation({
    mutationFn: tasksApi.stop,
    onSuccess: () => {
      message.success("任务已停止");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    }
  });

  const handleSubmit = (values: any) => {
    // 转换文本区域输入为数组（每行一个元素）
    const processListField = (field: string) => {
      if (values[field]) {
        return values[field]
          .split("\n")
          .map((item: string) => item.trim())
          .filter((item: string) => item.length > 0);
      }
      return undefined;
    };

    const requestData: TaskCreateRequest = {
      ...values,
      xhs_note_url_list: processListField("xhs_note_url_list"),
      xhs_creator_url_list: processListField("xhs_creator_url_list"),
      weibo_specified_id_list: processListField("weibo_specified_id_list"),
      weibo_creator_id_list: processListField("weibo_creator_id_list"),
      tieba_specified_id_list: processListField("tieba_specified_id_list"),
      tieba_name_list: processListField("tieba_name_list"),
      tieba_creator_url_list: processListField("tieba_creator_url_list"),
      bili_creator_id_list: processListField("bili_creator_id_list"),
      bili_specified_id_list: processListField("bili_specified_id_list"),
      dy_specified_id_list: processListField("dy_specified_id_list"),
      dy_creator_id_list: processListField("dy_creator_id_list"),
      ks_specified_id_list: processListField("ks_specified_id_list"),
      ks_creator_id_list: processListField("ks_creator_id_list"),
      zhihu_creator_url_list: processListField("zhihu_creator_url_list"),
      zhihu_specified_id_list: processListField("zhihu_specified_id_list")
    };

    createMutation.mutate(requestData);
  };

  const handleStop = (taskId: string) => {
    Modal.confirm({
      title: "确认停止",
      content: `确定要停止任务 ${taskId} 吗？`,
      okText: "确认",
      okType: "danger",
      cancelText: "取消",
      onOk: () => stopMutation.mutate(taskId)
    });
  };

  // 根据平台和爬虫类型渲染特定字段
  const renderPlatformSpecificFields = (
    platform: string,
    crawlerType: string
  ) => {
    if (!platform) return null;

    const fields: JSX.Element[] = [];

    // 小红书
    if (platform === "xhs") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="xhs_note_url_list"
            name="xhs_note_url_list"
            label="小红书笔记 URL 列表"
            tooltip="每行一个完整的笔记URL（需包含 xsec_token 和 xsec_source 参数）"
          >
            <Input.TextArea
              rows={4}
              placeholder="https://www.xiaohongshu.com/explore/xxx?xsec_token=xxx&xsec_source=pc_feed"
            />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="xhs_creator_url_list"
            name="xhs_creator_url_list"
            label="小红书创作者 URL 列表"
            tooltip="每行一个完整的创作者主页URL（需包含 xsec_token 和 xsec_source 参数）"
          >
            <Input.TextArea
              rows={4}
              placeholder="https://www.xiaohongshu.com/user/profile/xxx?xsec_token=xxx&xsec_source=pc_search"
            />
          </Form.Item>
        );
      }
    }

    // 微博
    if (platform === "wb") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="weibo_specified_id_list"
            name="weibo_specified_id_list"
            label="微博帖子 ID 列表"
            tooltip="每行一个帖子ID"
          >
            <Input.TextArea rows={4} placeholder="5180657661643376" />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="weibo_creator_id_list"
            name="weibo_creator_id_list"
            label="微博创作者 ID 列表"
            tooltip="每行一个创作者ID"
          >
            <Input.TextArea rows={4} placeholder="2172061270" />
          </Form.Item>
        );
      }
    }

    // 贴吧
    if (platform === "tieba") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="tieba_specified_id_list"
            name="tieba_specified_id_list"
            label="贴吧帖子 ID 列表"
            tooltip="每行一个帖子ID"
          >
            <Input.TextArea rows={4} placeholder="9815127841" />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="tieba_creator_url_list"
            name="tieba_creator_url_list"
            label="贴吧创作者 URL 列表"
            tooltip="每行一个完整的创作者主页URL"
          >
            <Input.TextArea
              rows={4}
              placeholder="https://tieba.baidu.com/home/main/?id=tb.1.xxx&fr=frs"
            />
          </Form.Item>
        );
      }
      // 贴吧名称列表（适用于搜索类型）
      if (crawlerType === "search") {
        fields.push(
          <Form.Item
            key="tieba_name_list"
            name="tieba_name_list"
            label="贴吧名称列表"
            tooltip="每行一个贴吧名称"
          >
            <Input.TextArea rows={4} placeholder="盗墓笔记" />
          </Form.Item>
        );
      }
    }

    // B站
    if (platform === "bili") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="bili_specified_id_list"
            name="bili_specified_id_list"
            label="B站视频 BVID 列表"
            tooltip="每行一个视频BVID"
          >
            <Input.TextArea rows={4} placeholder="BV1d54y1g7db" />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="bili_creator_id_list"
            name="bili_creator_id_list"
            label="B站创作者 ID 列表"
            tooltip="每行一个UP主ID"
          >
            <Input.TextArea rows={4} placeholder="434377496" />
          </Form.Item>
        );
      }
    }

    // 抖音
    if (platform === "dy") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="dy_specified_id_list"
            name="dy_specified_id_list"
            label="抖音视频 ID 列表"
            tooltip="每行一个视频ID"
          >
            <Input.TextArea rows={4} placeholder="7566756334578830627" />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="dy_creator_id_list"
            name="dy_creator_id_list"
            label="抖音创作者 ID 列表"
            tooltip="每行一个创作者sec_id"
          >
            <Input.TextArea
              rows={4}
              placeholder="MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE"
            />
          </Form.Item>
        );
      }
    }

    // 快手
    if (platform === "ks") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="ks_specified_id_list"
            name="ks_specified_id_list"
            label="快手视频 ID 列表"
            tooltip="每行一个视频ID"
          >
            <Input.TextArea rows={4} placeholder="3xf8enb8dbj6uig" />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="ks_creator_id_list"
            name="ks_creator_id_list"
            label="快手创作者 ID 列表"
            tooltip="每行一个创作者ID"
          >
            <Input.TextArea rows={4} placeholder="3x4sm73aye7jq7i" />
          </Form.Item>
        );
      }
    }

    // 知乎
    if (platform === "zhihu") {
      if (crawlerType === "detail") {
        fields.push(
          <Form.Item
            key="zhihu_specified_id_list"
            name="zhihu_specified_id_list"
            label="知乎内容 URL 列表"
            tooltip="每行一个完整的内容URL（支持回答、文章、视频、问题）"
          >
            <Input.TextArea
              rows={4}
              placeholder="https://www.zhihu.com/question/826896610/answer/4885821440"
            />
          </Form.Item>
        );
      } else if (crawlerType === "creator") {
        fields.push(
          <Form.Item
            key="zhihu_creator_url_list"
            name="zhihu_creator_url_list"
            label="知乎创作者 URL 列表"
            tooltip="每行一个完整的创作者主页URL"
          >
            <Input.TextArea
              rows={4}
              placeholder="https://www.zhihu.com/people/yd1234567"
            />
          </Form.Item>
        );
      }
    }

    if (crawlerType === "search") {
      fields.push(
        <Form.Item
          name="keywords"
          label="关键词"
          tooltip="多个关键词用逗号分隔"
        >
          <Input placeholder="例如: 美食,旅游,摄影" />
        </Form.Item>
      );
    }

    return fields.length > 0 ? (
      <>
        <Divider orientation="left">平台特定配置</Divider>
        {fields}
      </>
    ) : null;
  };

  const columns = [
    {
      title: "任务 ID",
      dataIndex: "task_id",
      key: "task_id",
      width: 200,
      render: (taskId: string) => (
        <span style={{ fontFamily: "monospace", fontSize: 12 }}>{taskId}</span>
      )
    },
    {
      title: "平台",
      dataIndex: "platform",
      key: "platform",
      width: 100,
      render: (platform: string) => (
        <Tag color="blue">{platform.toUpperCase()}</Tag>
      )
    },
    {
      title: "类型",
      dataIndex: "crawler_type",
      key: "crawler_type",
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => {
        const config = TASK_STATUS_MAP[
          status as keyof typeof TASK_STATUS_MAP
        ] || {
          color: "default",
          text: status
        };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: formatDateTime
    },
    {
      title: "操作",
      key: "action",
      width: 100,
      render: (_: any, record: any) => (
        <Button
          type="link"
          danger
          onClick={() => handleStop(record.task_id)}
          disabled={["SUCCESS", "FAILURE", "REVOKED"].includes(record.status)}
        >
          停止
        </Button>
      )
    }
  ];

  return (
    <div>
      <Card
        title="任务管理"
        extra={
          <Button type="primary" onClick={() => setIsModalOpen(true)}>
            创建任务
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasksData?.items || []}
          rowKey="task_id"
          loading={isLoading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: tasksData?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size);
            }
          }}
        />
      </Card>

      <Modal
        title="创建爬虫任务"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
          setSelectedPlatform("");
          setSelectedCrawlerType("");
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            enable_checkpoint: false,
            max_notes_count: 10,
            enable_comments: true,
            enable_sub_comments: false,
            max_comments_count: 20
          }}
        >
          <Form.Item
            name="platform"
            label="平台"
            rules={[{ required: true, message: "请选择平台" }]}
          >
            <Select
              options={PLATFORM_OPTIONS}
              placeholder="请选择平台"
              onChange={(value) => setSelectedPlatform(value)}
            />
          </Form.Item>

          <Form.Item
            name="crawler_type"
            label="爬虫类型"
            rules={[{ required: true, message: "请选择爬虫类型" }]}
          >
            <Select
              options={CRAWLER_TYPE_OPTIONS}
              placeholder="请选择爬虫类型"
              onChange={(value) => setSelectedCrawlerType(value)}
            />
          </Form.Item>

          {/* 平台特定配置 */}
          {renderPlatformSpecificFields(selectedPlatform, selectedCrawlerType)}

          <Divider />

          <Form.Item
            name="max_notes_count"
            label="最大采集数量"
            rules={[{ required: true, message: "请输入最大采集数量" }]}
          >
            <InputNumber min={1} max={10000} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            name="enable_checkpoint"
            label="启用断点续爬"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="checkpoint_id"
            label="断点 ID"
            tooltip="用于恢复之前的爬取进度"
          >
            <Input placeholder="留空则自动生成" />
          </Form.Item>

          <Form.Item
            name="enable_comments"
            label="采集评论"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="max_comments_count"
            label="最大评论数量"
            rules={[{ required: true, message: "请输入最大评论数量" }]}
            tooltip="每条内容最多采集的评论数量"
          >
            <InputNumber min={1} max={500} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            name="enable_sub_comments"
            label="采集子评论"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Tasks;
