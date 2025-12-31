import { Tree, Input, Button, Space, Dropdown, Modal, message, Spin } from "antd";
import type { DataNode as AntdDataNode, TreeProps } from "antd/es/tree";
import {
  FolderOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  MergeCellsOutlined,
  SplitCellsOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { useState, useMemo, useEffect, Key } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import type { HotspotDetail, ClusterInfo, HotspotStatus } from "@/types/api";
import { SplitClusterModal } from "./SplitClusterModal";

const { Search } = Input;

// 扩展 DataNode 以包含自定义数据
interface DataNode extends AntdDataNode {
  data?: HotspotDetail;
}

interface HotspotTreeViewProps {
  status?: HotspotStatus;
  onHotspotSelect?: (hotspot: HotspotDetail) => void;
  onRefresh?: () => void;
}

export function HotspotTreeView({
  status,
  onHotspotSelect,
  onRefresh,
}: HotspotTreeViewProps) {
  const queryClient = useQueryClient();
  const [expandedKeys, setExpandedKeys] = useState<Key[]>([]);
  const [searchValue, setSearchValue] = useState("");
  const [selectedKeys, setSelectedKeys] = useState<Key[]>([]);
  const [mergeModalVisible, setMergeModalVisible] = useState(false);
  const [splitModalVisible, setSplitModalVisible] = useState(false);
  const [selectedClusters, setSelectedClusters] = useState<number[]>([]);
  const [currentCluster, setCurrentCluster] = useState<{
    id: number;
    name: string;
  } | null>(null);

  // 获取所有聚簇
  const { data: clustersData, isLoading: clustersLoading } = useQuery({
    queryKey: ["clusters"],
    queryFn: () => hotspotsApi.listClusters(),
  });

  // 获取所有热点
  const { data: hotspotsData, isLoading: hotspotsLoading } = useQuery({
    queryKey: ["hotspots", { page: 1, page_size: 1000, status }],
    queryFn: () =>
      hotspotsApi.list({ page: 1, page_size: 1000, status }),
  });

  // 删除聚簇
  const deleteClusterMutation = useMutation({
    mutationFn: hotspotsApi.deleteCluster,
    onSuccess: () => {
      message.success("聚簇已删除");
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
      queryClient.invalidateQueries({ queryKey: ["hotspots"] });
      onRefresh?.();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    },
  });

  // 合并聚簇
  const mergeClustersMutation = useMutation({
    mutationFn: hotspotsApi.mergeClusters,
    onSuccess: () => {
      message.success("聚簇已合并");
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
      queryClient.invalidateQueries({ queryKey: ["hotspots"] });
      setMergeModalVisible(false);
      setSelectedClusters([]);
      onRefresh?.();
    },
    onError: (error: any) => {
      message.error(`合并失败: ${error.message}`);
    },
  });

  // 更新聚簇名称
  const updateClusterMutation = useMutation({
    mutationFn: ({ clusterId, name }: { clusterId: number; name: string }) =>
      hotspotsApi.updateCluster(clusterId, { cluster_name: name }),
    onSuccess: () => {
      message.success("聚簇名称已更新");
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
      onRefresh?.();
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message}`);
    },
  });

  // 构建树形数据
  const treeData = useMemo((): DataNode[] => {
    const clusters = clustersData?.items || [];
    const hotspots = hotspotsData?.items || [];

    // 创建聚簇节点的映射
    const clusterMap = new Map<number, DataNode>();

    clusters.forEach((cluster: ClusterInfo) => {
      clusterMap.set(cluster.id, {
        key: `cluster-${cluster.id}`,
        title: cluster.cluster_name,
        icon: (props: any) =>
          props.expanded ? <FolderOpenOutlined /> : <FolderOutlined />,
        children: [],
        isLeaf: false,
      });
    });

    // 未分组的热点节点
    const ungroupedHotspots: DataNode[] = [];

    // 将热点添加到对应的聚簇或未分组列表
    hotspots.forEach((hotspot: HotspotDetail) => {
      const hotspotNode: DataNode = {
        key: `hotspot-${hotspot.id}`,
        title: hotspot.keyword,
        icon: <FileTextOutlined />,
        isLeaf: true,
        data: hotspot,
      };

      if (hotspot.cluster_id && clusterMap.has(hotspot.cluster_id)) {
        const clusterNode = clusterMap.get(hotspot.cluster_id)!;
        if (clusterNode.children) {
          clusterNode.children.push(hotspotNode);
        }
      } else {
        ungroupedHotspots.push(hotspotNode);
      }
    });

    const result: DataNode[] = [];

    // 添加有成员的聚簇
    clusterMap.forEach((node) => {
      if (node.children && node.children.length > 0) {
        result.push(node);
      }
    });

    // 添加未分组的热点
    if (ungroupedHotspots.length > 0) {
      result.push({
        key: "ungrouped",
        title: `未分组 (${ungroupedHotspots.length})`,
        icon: (props: any) =>
          props.expanded ? <FolderOpenOutlined /> : <FolderOutlined />,
        children: ungroupedHotspots,
        isLeaf: false,
      });
    }

    return result;
  }, [clustersData, hotspotsData]);

  // 过滤树形数据
  const filteredTreeData = useMemo(() => {
    if (!searchValue) return treeData;

    const filterNode = (node: DataNode): DataNode | null => {
      const title = String(node.title).toLowerCase();
      const matches = title.includes(searchValue.toLowerCase());

      if (node.children) {
        const filteredChildren = node.children
          .map(filterNode)
          .filter((child): child is DataNode => child !== null);

        if (filteredChildren.length > 0 || matches) {
          return {
            ...node,
            children: filteredChildren,
          };
        }
      }

      return matches ? node : null;
    };

    return treeData
      .map(filterNode)
      .filter((node): node is DataNode => node !== null);
  }, [treeData, searchValue]);

  // 自动展开搜索结果
  useEffect(() => {
    if (searchValue) {
      const keys: Key[] = [];
      const collectKeys = (nodes: DataNode[]) => {
        nodes.forEach((node) => {
          if (node.children && node.children.length > 0) {
            keys.push(node.key);
            collectKeys(node.children);
          }
        });
      };
      collectKeys(filteredTreeData);
      setExpandedKeys(keys);
    }
  }, [searchValue, filteredTreeData]);

  const onSelect: TreeProps["onSelect"] = (selectedKeys, info) => {
    setSelectedKeys(selectedKeys);
    const node = info.node as DataNode;
    if (node.isLeaf && node.data) {
      onHotspotSelect?.(node.data);
    }
  };

  const onExpand: TreeProps["onExpand"] = (expandedKeys) => {
    setExpandedKeys(expandedKeys);
  };

  // 聚簇右键菜单
  const getClusterMenuItems = (clusterId: number, clusterName: string) => [
    {
      key: "rename",
      icon: <EditOutlined />,
      label: "重命名",
      onClick: () => {
        Modal.confirm({
          title: "重命名聚簇",
          content: (
            <Input
              defaultValue={clusterName}
              id="cluster-rename-input"
              placeholder="请输入新名称"
            />
          ),
          onOk: () => {
            const input = document.getElementById(
              "cluster-rename-input"
            ) as HTMLInputElement;
            const newName = input?.value.trim();
            if (newName && newName !== clusterName) {
              updateClusterMutation.mutate({ clusterId, name: newName });
            }
          },
        });
      },
    },
    {
      key: "split",
      icon: <SplitCellsOutlined />,
      label: "拆分聚簇",
      onClick: () => {
        setCurrentCluster({ id: clusterId, name: clusterName });
        setSplitModalVisible(true);
      },
    },
    {
      key: "merge",
      icon: <MergeCellsOutlined />,
      label: "合并到...",
      onClick: () => {
        setSelectedClusters([clusterId]);
        setMergeModalVisible(true);
      },
    },
    {
      key: "delete",
      icon: <DeleteOutlined />,
      label: "删除聚簇",
      danger: true,
      onClick: () => {
        Modal.confirm({
          title: "确认删除",
          content: `确定要删除聚簇"${clusterName}"吗？聚簇内的热点将变为未分组状态。`,
          okText: "删除",
          okType: "danger",
          onOk: () => deleteClusterMutation.mutate(clusterId),
        });
      },
    },
  ];

  // 自定义标题渲染，支持右键菜单
  const titleRender = (nodeData: DataNode) => {
    const keyStr = String(nodeData.key);
    const titleText = typeof nodeData.title === 'function' ? '' : String(nodeData.title || '');

    if (keyStr.startsWith("cluster-")) {
      const clusterId = parseInt(keyStr.replace("cluster-", ""));
      return (
        <Dropdown
          menu={{ items: getClusterMenuItems(clusterId, titleText) }}
          trigger={["contextMenu"]}
        >
          <span style={{ userSelect: "none" }}>{titleText}</span>
        </Dropdown>
      );
    }

    return <span>{titleText}</span>;
  };

  const handleMergeClusters = () => {
    if (selectedClusters.length < 2) {
      message.warning("请至少选择2个聚簇进行合并");
      return;
    }

    mergeClustersMutation.mutate({
      source_cluster_ids: selectedClusters,
    });
  };

  const isLoading = clustersLoading || hotspotsLoading;

  return (
    <div style={{ height: "100%" }}>
      <Space direction="vertical" style={{ width: "100%", marginBottom: 16 }}>
        <Search
          placeholder="搜索热词或聚簇..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          allowClear
        />
        <Button
          icon={<MergeCellsOutlined />}
          onClick={() => setMergeModalVisible(true)}
          block
        >
          合并聚簇
        </Button>
      </Space>

      <Spin spinning={isLoading}>
        <Tree
          showIcon
          selectedKeys={selectedKeys}
          expandedKeys={expandedKeys}
          onSelect={onSelect}
          onExpand={onExpand}
          treeData={filteredTreeData}
          titleRender={titleRender}
          height={600}
          virtual
        />
      </Spin>

      {/* 合并聚簇弹窗 */}
      <Modal
        title="合并聚簇"
        open={mergeModalVisible}
        onOk={handleMergeClusters}
        onCancel={() => {
          setMergeModalVisible(false);
          setSelectedClusters([]);
        }}
        okText="合并"
        cancelText="取消"
      >
        <p>请选择要合并的聚簇（至少选择2个）：</p>
        {clustersData?.items.map((cluster) => (
          <div key={cluster.id} style={{ marginBottom: 8 }}>
            <label>
              <input
                type="checkbox"
                checked={selectedClusters.includes(cluster.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedClusters([...selectedClusters, cluster.id]);
                  } else {
                    setSelectedClusters(
                      selectedClusters.filter((id) => id !== cluster.id)
                    );
                  }
                }}
                style={{ marginRight: 8 }}
              />
              {cluster.cluster_name} ({cluster.member_count} 个热点)
            </label>
          </div>
        ))}
      </Modal>

      {/* 拆分聚簇弹窗 */}
      {currentCluster && (
        <SplitClusterModal
          visible={splitModalVisible}
          clusterId={currentCluster.id}
          clusterName={currentCluster.name}
          hotspots={
            hotspotsData?.items.filter(
              (h) => h.cluster_id === currentCluster.id
            ) || []
          }
          onClose={() => {
            setSplitModalVisible(false);
            setCurrentCluster(null);
          }}
        />
      )}
    </div>
  );
}
