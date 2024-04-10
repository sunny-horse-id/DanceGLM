import axios from 'axios';
const baseURL = '/api';

const instance = axios.create({ baseURL });

//请求拦截器
instance.interceptors.request.use(
    (config) => {
        return config
    },
    (err) => {
        return Promise.reject(err);
    }
)

//响应拦截器
instance.interceptors.response.use(
    result => {
        return result
    },
    err => {
        return Promise.reject(err);
    }
)

export default instance;