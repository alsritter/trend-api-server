import { Card, Space, Button, message } from "antd";
import { ReloadOutlined, MergeCellsOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { clustersApi } from "@/api/clusters";
import { hotspotsApi } from "@/api/hotspots";
import type { ClusterInfo } from "@/types/api";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import { HotspotsFilter } from "./HotspotsFilter";
import { ClustersTable } from "./ClustersTable";
import { ClusterExpandedRow } from "./ClusterExpandedRow";
import { PLATFORM_NAME_TO_CODE } from "./constants";

import { EditClusterModal } from "./EditClusterModal";
import { MergeClustersModal } from "./MergeClustersModal";

function Hotspots() {
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([]);

  // 分页状态
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);

  // 过滤条件状态
  const [filterStatus, setFilterStatus] = useState<string[]>([]);
  const [excludeStatus, setExcludeStatus] = useState<string[]>([]);
  const [filterPlatforms, setFilterPlatforms] = useState<string[]>([]);
  const [filterDateRange, setFilterDateRange] = useState<
    [Dayjs | null, Dayjs | null] | null
  >(null);
  const [searchKeyword, setSearchKeyword] = useState<string>("");

  // 编辑聚簇名称
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<ClusterInfo | null>(
    null
  );

  // 合并聚簇
  const [mergeModalVisible, setMergeModalVisible] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [selectedClusters, setSelectedClusters] = useState<ClusterInfo[]>([]);

  // 查询聚簇列表
  const {
    data: clustersData,
    isLoading: clustersLoading,
    refetch: refetchClusters
  } = useQuery({
    queryKey: [
      "clusters",
      page,
      pageSize,
      filterStatus,
      excludeStatus,
      filterPlatforms,
      filterDateRange,
      searchKeyword
    ],
    queryFn: async () => {
      const params: any = {
        page,
        page_size: pageSize
      };
      if (filterStatus.length > 0) params.status = filterStatus.join(",");
      if (excludeStatus.length > 0)
        params.exclude_status = excludeStatus.join(",");
      if (filterPlatforms.length > 0)
        params.platforms = filterPlatforms.join(",");
      if (filterDateRange?.[0])
        params.start_time = filterDateRange[0].format("YYYY-MM-DDTHH:mm:ss");
      if (filterDateRange?.[1])
        params.end_time = filterDateRange[1].format("YYYY-MM-DDTHH:mm:ss");
      if (searchKeyword) params.keyword = searchKeyword;

      return clustersApi.list(params);
    }
  });

  // 更新聚簇名称
  const updateClusterMutation = useMutation({
    mutationFn: ({
      clusterId,
      clusterName
    }: {
      clusterId: number;
      clusterName: string;
    }) => clustersApi.update(clusterId, { cluster_name: clusterName }),
    onSuccess: () => {
      message.success("聚簇名称更新成功");
      setEditModalVisible(false);
      setEditingCluster(null);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message}`);
    }
  });

  // 删除聚簇
  const deleteClusterMutation = useMutation({
    mutationFn: (clusterId: number) => clustersApi.delete(clusterId),
    onSuccess: () => {
      message.success("聚簇删除成功");
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 验证成功 - 更新聚簇代表热点状态为已验证
  const validateSuccessMutation = useMutation({
    mutationFn: async (cluster: ClusterInfo) => {
      if (!cluster.selected_hotspot_id) {
        throw new Error("该聚簇没有绑定代表热点");
      }
      return hotspotsApi.updateStatusAndSetRepresentative(
        cluster.selected_hotspot_id,
        { status: "validated", set_as_representative: true }
      );
    },
    onSuccess: () => {
      message.success("热点已标记为验证成功");
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`验证失败: ${error.message}`);
    }
  });

  // 触发爬取 - 为聚簇代表热点触发爬虫任务
  const triggerCrawlMutation = useMutation({
    mutationFn: async (cluster: ClusterInfo) => {
      if (!cluster.selected_hotspot_id) {
        throw new Error("该聚簇没有绑定代表热点");
      }
      // 根据聚簇的平台分布自动选择要爬取的平台，并转换为平台代码
      const platforms = cluster.platforms
        .map(p => PLATFORM_NAME_TO_CODE[p.platform] || p.platform)
        .filter(Boolean); // 过滤掉无效的平台代码
      
      if (platforms.length === 0) {
        throw new Error("没有找到有效的平台");
      }
      
      return hotspotsApi.triggerCrawl({
        hotspot_id: cluster.selected_hotspot_id,
        platforms: platforms,
        crawler_type: "search",
        max_notes_count: 50,
        enable_comments: true,
        enable_sub_comments: false,
        max_comments_count: 20
      });
    },
    onSuccess: (data) => {
      message.success(`成功创建 ${data.total_tasks} 个爬虫任务`);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`触发爬取失败: ${error.message}`);
    }
  });

  // 合并聚簇
  const mergeClustersMutation = useMutation({
    mutationFn: (data: {
      source_cluster_ids: number[];
      target_cluster_name?: string;
    }) => clustersApi.merge(data),
    onSuccess: () => {
      message.success("聚簇合并成功");
      setMergeModalVisible(false);
      setSelectedRowKeys([]);
      setSelectedClusters([]);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`合并失败: ${error.message}`);
    }
  });

  // 重置过滤条件
  const handleResetFilters = () => {
    setFilterStatus([]);
    setExcludeStatus([]);
    setFilterPlatforms([]);
    setFilterDateRange(null);
    setSearchKeyword("");
    setPage(1);
  };

  // 快速过滤待审核热词（3小时到2天之间的 pending_validation 状态）
  const handleQuickFilterPendingValidation = () => {
    const now = dayjs();
    const endOfToday = now.endOf("day");
    const twoDaysAgo = now.subtract(2, "day");

    setFilterStatus(["pending_validation"]);
    setExcludeStatus([]);
    setFilterPlatforms(["小红书", "抖音"]);
    setFilterDateRange([twoDaysAgo, endOfToday]);
    setPage(1);
    message.info("已应用待审核热词过滤条件（2天前至今天结束，小红书和抖音平台）");
  };

  // 处理展开/收起聚簇
  const handleExpandChange = (expanded: boolean, record: ClusterInfo) => {
    if (expanded) {
      setExpandedRowKeys([...expandedRowKeys, record.id]);
    } else {
      setExpandedRowKeys(expandedRowKeys.filter((key) => key !== record.id));
    }
  };

  // 处理编辑聚簇
  const handleEdit = (cluster: ClusterInfo) => {
    setEditingCluster(cluster);
    setEditModalVisible(true);
  };

  // 处理删除聚簇
  const handleDelete = (clusterId: number) => {
    deleteClusterMutation.mutate(clusterId);
  };

  // 处理验证成功
  const handleValidateSuccess = (cluster: ClusterInfo) => {
    validateSuccessMutation.mutate(cluster);
  };

  // 处理触发爬取
  const handleTriggerCrawl = (cluster: ClusterInfo) => {
    triggerCrawlMutation.mutate(cluster);
  };

  // 处理编辑确认
  const handleEditConfirm = (clusterName: string) => {
    if (editingCluster) {
      updateClusterMutation.mutate({
        clusterId: editingCluster.id,
        clusterName
      });
    }
  };

  // 处理编辑取消
  const handleEditCancel = () => {
    setEditModalVisible(false);
    setEditingCluster(null);
  };

  // 处理行选择
  const handleSelectChange = (
    selectedKeys: React.Key[],
    selectedRows: ClusterInfo[]
  ) => {
    setSelectedRowKeys(selectedKeys as number[]);
    setSelectedClusters(selectedRows);
  };

  // 处理打开合并模态框
  const handleOpenMergeModal = () => {
    if (selectedRowKeys.length < 2) {
      message.warning("请至少选择2个聚簇进行合并");
      return;
    }
    setMergeModalVisible(true);
  };

  // 处理合并确认
  const handleMergeConfirm = (targetClusterName?: string) => {
    mergeClustersMutation.mutate({
      source_cluster_ids: selectedRowKeys,
      target_cluster_name: targetClusterName
    });
  };

  // 处理合并取消
  const handleMergeCancel = () => {
    setMergeModalVisible(false);
  };

  // 处理分页变化
  const handlePageChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  return (
    <div style={{ padding: "24px" }}>
      <Card
        title="热点聚簇管理"
        extra={
          <Space>
            <Button
              icon={<MergeCellsOutlined />}
              onClick={handleOpenMergeModal}
              disabled={selectedRowKeys.length < 2}
            >
              合并聚簇 ({selectedRowKeys.length})
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchClusters()}
              loading={clustersLoading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <HotspotsFilter
          searchKeyword={searchKeyword}
          filterStatus={filterStatus}
          excludeStatus={excludeStatus}
          filterPlatforms={filterPlatforms}
          filterDateRange={filterDateRange}
          onSearchChange={setSearchKeyword}
          onStatusChange={setFilterStatus}
          onExcludeStatusChange={setExcludeStatus}
          onPlatformsChange={setFilterPlatforms}
          onDateRangeChange={setFilterDateRange}
          onReset={handleResetFilters}
          onQuickFilterPendingValidation={handleQuickFilterPendingValidation}
        />

        <ClustersTable
          data={clustersData?.items || []}
          loading={clustersLoading}
          total={clustersData?.count || 0}
          page={page}
          pageSize={pageSize}
          expandedRowKeys={expandedRowKeys}
          searchKeyword={searchKeyword}
          selectedRowKeys={selectedRowKeys}
          onExpandChange={handleExpandChange}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onValidateSuccess={handleValidateSuccess}
          onTriggerCrawl={handleTriggerCrawl}
          onSelectChange={handleSelectChange}
          onPageChange={handlePageChange}
          renderExpandedRow={(record) => (
            <ClusterExpandedRow clusterId={record.id} />
          )}
        />
      </Card>

      <EditClusterModal
        visible={editModalVisible}
        cluster={editingCluster}
        loading={updateClusterMutation.isPending}
        onOk={handleEditConfirm}
        onCancel={handleEditCancel}
      />

      <MergeClustersModal
        visible={mergeModalVisible}
        clusters={selectedClusters}
        loading={mergeClustersMutation.isPending}
        onOk={handleMergeConfirm}
        onCancel={handleMergeCancel}
      />
    </div>
  );
}

export default Hotspots;
