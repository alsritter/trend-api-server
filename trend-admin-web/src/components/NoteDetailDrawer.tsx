import { Drawer, Descriptions, Table, Tabs, Spin, Empty } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { contentsApi } from '@/api/contents'
import { formatDateTime } from '@/utils/format'
import type { Note, Comment } from '@/types/api'
import { useState } from 'react'

interface NoteDetailDrawerProps {
  visible: boolean
  onClose: () => void
  note: Note | null
  platform: string
}

function NoteDetailDrawer({ visible, onClose, note, platform }: NoteDetailDrawerProps) {
  const [commentPage, setCommentPage] = useState(1)
  const [commentPageSize, setCommentPageSize] = useState(20)

  // 获取评论列表
  const { data: commentsData, isLoading: commentsLoading } = useQuery({
    queryKey: ['comments', platform, note?.note_id, commentPage, commentPageSize],
    queryFn: () =>
      contentsApi.getComments(platform, {
        note_id: note?.note_id || '',
        page: commentPage,
        page_size: commentPageSize,
      }),
    enabled: visible && !!note?.note_id,
  })

  if (!note) return null

  // 通用字段
  const generalItems = [
    { key: 'note_id', label: '笔记ID', children: note.note_id },
    { key: 'title', label: '标题', children: note.title || note.desc?.substring(0, 50) },
    { key: 'nickname', label: '作者', children: note.nickname || note.user_name },
    { key: 'user_id', label: '作者ID', children: note.user_id },
  ]

  // 平台特定字段
  const platformSpecificItems = () => {
    const items: any[] = []

    if (platform === 'xhs') {
      items.push(
        { key: 'type', label: '类型', children: note.type === 'video' ? '视频' : '图文' },
        { key: 'liked_count', label: '点赞数', children: note.liked_count },
        { key: 'collected_count', label: '收藏数', children: note.collected_count },
        { key: 'comment_count', label: '评论数', children: note.comment_count },
        { key: 'share_count', label: '分享数', children: note.share_count },
      )
    } else if (platform === 'dy' || platform === 'ks') {
      items.push(
        { key: 'video_play_count', label: '播放量', children: note.video_play_count },
        { key: 'liked_count', label: '点赞数', children: note.liked_count },
        { key: 'comment_count', label: '评论数', children: note.comment_count },
        { key: 'video_share_count', label: '分享数', children: note.video_share_count },
      )
    } else if (platform === 'bili') {
      items.push(
        { key: 'video_play_count', label: '播放量', children: note.video_play_count },
        { key: 'video_danmaku', label: '弹幕数', children: note.video_danmaku },
        { key: 'video_comment', label: '评论数', children: note.video_comment },
        { key: 'video_like_count', label: '点赞数', children: note.video_like_count },
      )
    } else if (platform === 'wb') {
      items.push(
        { key: 'attitudes_count', label: '点赞数', children: note.attitudes_count },
        { key: 'comments_count', label: '评论数', children: note.comments_count },
        { key: 'reposts_count', label: '转发数', children: note.reposts_count },
      )
    } else if (platform === 'tieba') {
      items.push(
        { key: 'total_replay_page', label: '评论页数', children: note.total_replay_page },
        { key: 'view_count', label: '浏览量', children: note.view_count },
      )
    } else if (platform === 'zhihu') {
      items.push(
        { key: 'content_type', label: '内容类型', children: note.content_type },
        { key: 'voteup_count', label: '点赞数', children: note.voteup_count },
        { key: 'comment_count', label: '评论数', children: note.comment_count },
      )
    }

    return items
  }

  const timeItems = [
    { key: 'create_time', label: '发布时间', children: note.create_time ? formatDateTime(note.create_time) : '-' },
    { key: 'update_time', label: '更新时间', children: note.update_time ? formatDateTime(note.update_time) : '-' },
  ]

  const contentItems = [
    { 
      key: 'desc', 
      label: '内容描述', 
      children: <div style={{ maxHeight: 300, overflow: 'auto', whiteSpace: 'pre-wrap' }}>{note.desc || note.content}</div>,
      span: 3 
    },
  ]

  // 评论列表列定义
  const commentColumns = [
    {
      title: '评论ID',
      dataIndex: 'comment_id',
      key: 'comment_id',
      width: 150,
      ellipsis: true,
    },
    {
      title: '用户',
      dataIndex: 'nickname',
      key: 'nickname',
      width: 120,
      render: (text: string, record: Comment) => text || record.user_name,
    },
    {
      title: '评论内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '点赞数',
      dataIndex: 'like_count',
      key: 'like_count',
      width: 100,
      render: (text: number) => text || 0,
    },
    {
      title: '子评论数',
      dataIndex: 'sub_comment_count',
      key: 'sub_comment_count',
      width: 100,
      render: (text: number) => text || 0,
    },
    {
      title: '发布时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: formatDateTime,
    },
  ]

  const tabItems = [
    {
      key: 'info',
      label: '笔记详情',
      children: (
        <Descriptions 
          bordered 
          column={3}
          size="small"
          items={[...generalItems, ...platformSpecificItems(), ...timeItems, ...contentItems]}
        />
      ),
    },
    {
      key: 'comments',
      label: `评论列表 (${commentsData?.total || 0})`,
      children: commentsLoading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin />
        </div>
      ) : (
        <Table
          columns={commentColumns}
          dataSource={commentsData?.items || []}
          rowKey="comment_id"
          size="small"
          pagination={{
            current: commentPage,
            pageSize: commentPageSize,
            total: commentsData?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条评论`,
            onChange: (newPage, newPageSize) => {
              setCommentPage(newPage)
              setCommentPageSize(newPageSize)
            },
          }}
          locale={{
            emptyText: <Empty description="暂无评论" />,
          }}
        />
      ),
    },
  ]

  return (
    <Drawer
      title="笔记详情"
      placement="right"
      width={1000}
      onClose={onClose}
      open={visible}
      destroyOnClose
    >
      <Tabs items={tabItems} defaultActiveKey="info" />
    </Drawer>
  )
}

export default NoteDetailDrawer
