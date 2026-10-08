import request from './request' 

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
    username: string,
    email: string,
    password: string,
    config_password: string,
    phone: string,
    nike_name: string,
    user_type: string,
}

export interface AuthResponse {
    message: string
    user: {
        id: number,
        username: string,
        email: string,
        phone: string,
        nike_name: string,
        avatar: string,
        user_type: string,
        is_verified: boolean,
        data_joined: string,
        last_login: string
    }
    access: string
    refresh: string
}

export const authApi = { 
    // 登录
    login: (data: LoginRequest) => {
        return request.post<AuthResponse>('/auth/login/', data)
    },

    // 注册
    register: (data: RegisterRequest) => {
        return request.post<AuthResponse>('/auth/register/', data)
    },

    // 登出
    logout: () => {
        return request.post('/auth/logout/')
    },

    // 获取用户信息
    getUserInfo: () => {
        return request.get('/auth/profile/')
    },

    // 修改密码
    changePassword: (data: { old_password: string; new_password: string }) => {
        return request.post('/auth/password/change/', data)
    },

    // 刷新 token
    refreshToken: (refresh: string) => {
        return request.post<{ access: string }>('/auth/token/refresh/', { refresh })
    },

    // 获取资料
    getProfile: () => {
        return request.get('/auth/profile/')
    },

    // 更新资料
    updateProfile: (data: Record<string, any>) => {
        return request.patch('/auth/profile/', data)
    },

    // 更新头像
    updateAvatar: (file: File) => {
        const form = new FormData()
        form.append('avatar', file)
        return request.post('/auth/profile/avatar/', form)
    },

    // 检查用户名是否存在
    checkUsername: (username: string) => {
        return request.post('/auth/check/username/', { username })
    },
}

// 用户管理 API（管理员）
export const usersApi = {
    getUsers: (params?: any) => request.get('/auth/', { params }),
    createUser: (data: any) => request.post('/auth/', data),
    updateUser: (id: number, data: any) => request.put(`/auth/${id}/`, data),
    deleteUser: (id: number) => request.delete(`/auth/${id}/`)
}