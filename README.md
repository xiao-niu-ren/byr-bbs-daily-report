# byr论坛每日新帖推送
> 目前支持兼职实习和招聘信息板块，想要添加板块可以在./auto.py的FETCH_LIST中仿照之前的格式动态添加

使用方式：

1. 在仓库的Settings-->Secrets中添加用户名（你的id）、密码session（可通过chrome抓包，在session中获取nforum[PASSWORD]的值） 示例：
    ```shell
   {
   "USERNAME": "BUPT123", 
   "PASSWORD_SESSION": "dh91db19d1919&&!^Biwbi1",
   # 下面两个可以不用管，也可以根据自己的推送回调方式实现（需要修改代码）
   "CALLBACK_URL": "https://www.callback.com",
   "WeChat_ID_LIST": "wx123,123@chatroom" #用,分隔，不能有空格
   }
    ```
3. 自动执行时间在./github/workflows/main.yml中有说明，cron表达式配置~