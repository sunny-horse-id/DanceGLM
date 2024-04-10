import request from "@/utils/request.js"

// 获取fbx和wav的地址
export const getAddressAPI = () => {
    return request.get('/address')
}