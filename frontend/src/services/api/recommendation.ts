import request from '@/utils/request'

export const recommendationApi = {
  // 获取推荐问题
  async getRecommendations(
    conversationHistory: string[] = [],
    roleName?: string
  ): Promise<string[]> {
    const params: any = {}
    if (roleName) {
      params.roleName = roleName
    }
    const response = await request.post<string[]>(
      '/recommendations/questions',
      conversationHistory,
      { params }
    )
    return response.data
  }
}

