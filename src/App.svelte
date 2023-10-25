<script>
    import {onMount} from 'svelte';
    import Pusher from 'pusher-js';

    let pusher;

    // Chat Implementation - Chat Channel 
    let channel;
    let prevChannelName;


    // Friend Implementation - Friend Channel
    let friendChannel;
    let prevFriendChannelName;


    let userEmail = 'ken@gmail.com';
    let receiverEmail = "";
    let message = '';

    //mock user info for test
    let name = 'Jack';  // User's name, should be initialized based on your app's user data
    let avatar =  "https://mdbcdn.b-cdn.net/img/new/avatars/2.webp";  // User's avatar URL, should be initialized based on your app's user data
    let userId = 1;  // should be initialized based on your app's user data

    let messages = [];
    let base_url = "http://localhost:5005";

    let newFriendEmail = "";

    
    // Chat Implementation - 模拟从profile那边拿到的main user信息
    let mainUserInfo = {email: userEmail, 
                        avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/1.webp', 
                        name: 'Main User',
                        userID: 1
                    };

    // Friend Implementation - Placeholder for friend list
    let friends = [

    ];

    /// NEW - Online user list
    let onlineUsers = [];
    let config;


    // Chat / Friend Implementation - Setup Pusher when the component is mounted
    onMount(async () => {
        Pusher.logToConsole = true;



        // Fetch Pusher configuration from the backend
        const response = await fetch(base_url+'/api/chat/config/');
        config = await response.json();

        // New - Unread: 刚登录进主界面需要把last chat user清空
        updateLastChatFriend("");
        // NEW - END

        // New - Online: need to update the pusher setup method
        pusher = new Pusher(config.key, {
            cluster: config.cluster,
            authEndpoint: base_url + "/api/chat/auth/",
            auth: {
                params: { email: userEmail },  // 无需 JSON.stringify，直接发送对象即可
            },
        });
        // NEW - END


        // Assume the chat page has already get the main user email from somewhere else
        // Friend Implementation - Fetch friend list for the main user when the page is loaded
        fetchFriendList(mainUserInfo["email"]);

        // Friend Implementation - Subscribe to the friend channel for the main user; Update automatically when adding new friend.
        friendChannel = pusher.subscribe(mainUserInfo["email"]);
        prevFriendChannelName = mainUserInfo["email"];
        friendChannel.bind('newfriend', data => receiveNewFriend(data));

        // New - Unread: unread notification channel
        friendChannel.bind('unread', data => receiveUnread(data));    
        // NEW - END

    })


    // New - Unread: Subscribe to the presence channnel to check the login status
    const subscribeOnlineChannel = async() => {
        
        // 订阅 presence 频道
        var presenceChannel = pusher.subscribe('presence-online');

        // 当用户连接时更新在线用户列表
        presenceChannel.bind('pusher:member_added', function(member) {
            // 用户上线，添加到在线列表
            onlineUsers = [...onlineUsers, member.id]; // 假设 member 对象有一个 ID 属性
            checkOnlineStatus(member.id, "online");
            rankOnlineUsers();
            console.log(member.id + " is online");
            console.log("onlineUsers: " + onlineUsers);
        });

        // 当用户断开连接时更新在线用户列表
        presenceChannel.bind('pusher:member_removed', function(member) {
            // 用户下线，从在线列表中移除
            onlineUsers = onlineUsers.filter(id => id !== member.id);
            checkOnlineStatus(member.id, "offline");
            rankOnlineUsers();
            console.log(member.id + " is offline");
            console.log("onlineUsers: " + onlineUsers);
        });

        // 获取初始的在线用户列表
        presenceChannel.bind('pusher:subscription_succeeded', function(members) {
            onlineUsers = Object.keys(members.members);
            updateOnlineStatus();
            rankOnlineUsers();
            console.log("onlineUsers: " + onlineUsers);
        });
    }
    // NEW - END

    // New - Unread: 正式版应该用不到,用于模拟重新登陆的过程测试的
    const unsubscribeOnlineChannel = async() => {
        pusher.unsubscribe('presence-online');
    }
    

    const updateOnlineStatus = () => {
        friends.forEach(friend => {
            if (onlineUsers.includes(friend.email)){
                friend.status = "online";
            } else {
                friend.status = "offline";
            }
        })
    }

    const checkOnlineStatus = (id, status) => {
        friends.forEach(friend => {
            if (friend.email == id){
                friend.status = status;
            }
        })
    }
    // NEW - END

    // New - Unread+Online: 基于unread和online状态对好友列表进行UI重新排序
    const rankOnlineUsers = () => {
        // Move the online users to the front of the list
        let onlineFriends = [];
        let offlineFriends = [];
        let unreadFriends = [];
        friends.forEach(friend => {
            if(friend.unread > 0){
                unreadFriends = [...unreadFriends, friend];
            }else{
                if (friend.status == "online"){
                onlineFriends = [...onlineFriends, friend];
                } else {
                    offlineFriends = [...offlineFriends, friend];
                }
            }
        })
        friends = [...unreadFriends,...onlineFriends, ...offlineFriends];
    }
    // New - END



    // Chat implementation - Send Message
    const submit = async () => {
        console.log("submit triggered");

        const message_body = JSON.stringify({
            userInfo: {
                userId,  // this could be the user's ID from your system
                name,  // the user's name from your system
                avatar,  // the user's avatar URL
            },
            receiverInfo:{
                    avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/5.webp', 
                    name: 'Lucy',
                    userId: 1,
                    status: friends.find(friend => friend.email == receiverEmail).status,
            },
            message,  // the message text
            userEmail,  // the email of the user sending the message
            receiverEmail,  // the email of the message recipient
        });

        await fetch(base_url+'/api/chat/message/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: message_body
        });

        message = '';  // clear the message input after successful sending
    }

    // Chat implementation - Channel name helper
    function getChannelName(username,receiver){
        // Sort the usernames
        const sortedUsernames = [username, receiver].sort();

        // Join with a delimiter
        const channelName = sortedUsernames[0] + "-" + sortedUsernames[1];

        return channelName;
    }

    // Chat implementation - Get chat history
    const fetchHistory = async () => {
        const response = await fetch(base_url + '/api/chat/history/',{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userEmail,
                receiverEmail,
            })
        });
        const data = await response.json();
        if (data && data.length > 0) {
                messages = data;
            } 
        console.log("history result: ", messages);
    }

    // Friend implementation - Get Friend List
    const fetchFriendList = async () => {
        const response = await fetch(base_url + '/api/chat/friendlist/',{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userEmail,
            })
        });
        const data = await response.json();
        if (data && data.length > 0) {
                friends = data;
                // New - Online: 获取好友列表后订阅presence channel，进而获取在线用户列表
                subscribeOnlineChannel();
                // New - END
                
            }
        console.log(friends)
    }

    // Friend implementation - Triggered by pusher friend channel; Add new friend to the existing list
    const receiveNewFriend = async(data) => {
        console.log("receiveNewFriend triggered");
        console.log(data);
        friends = [...friends, data];


        // New - Online: 为新好友更新在线状态
        updateOnlineStatus();
        rankOnlineUsers();
        // NEW - END
    }


    // Chat implementation - Send Message
    const addNewFriend = async () => {
        console.log("addNewFriend triggered");

        const message_body = JSON.stringify({
            userEmail,  // the email of the user sending the message
            userData: {
                email: mainUserInfo["email"],  
                name: mainUserInfo["name"],   // the user's name from your system
                avatar: mainUserInfo["avatar"],  // the user's avatar URL
                unread: 0, //这两个在实际implementation里也默认都填0即可，因为是新好友
                lastReadTime: 0,
                status: "online" //不会被实际用到，去掉也可以 (还是不会被用到,online纯粹由precence channel实现和这个没关系)

            },
            friendData:{ // 在dummy app中只有friendEmail会被backend用到，其他信息都是hardcode的，假设其他信息之后都能从Profile拿到在这里填入
                    avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/5.webp', 
                    name: 'Lucy',
                    userId: 1,
                    email: newFriendEmail,
                    unread: 0, //这两个在实际implementation里也默认都填0即可，因为是新好友
                    lastReadTime: 0,
                    status: "online" //不会被实际用到，去掉也可以
            },
        });

        await fetch(base_url+'/api/chat/addfriend/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: message_body
        });

        message = '';  // clear the message input after successful sending


    }



    // Chat implementation - UI messages update helper
    const receiveNewMessage = (data) =>{
        messages = [...messages, data];
    }

    // Chat implementation - Swicth the chatting user
    const switchReceiver = async () => {
        let newChannelName = getChannelName(userEmail, receiverEmail);
        if (channel) {
            channel.unbind('message'); 
            pusher.unsubscribe(prevChannelName); 
            // Clear the messages in current window
            messages = [];
        }
        channel = pusher.subscribe(newChannelName);
        
        console.log("switchReceiver triggered: ", newChannelName)

        prevChannelName = newChannelName

        // Fetch chat history when switching receiver
        fetchHistory();
        channel.bind('message', data => receiveNewMessage(data));

        // New - Unread: when switch receiver, update the last chat friend to db for main user
        updateLastChatFriend(receiverEmail);
        friends.forEach(friend => {
            if (friend.email == receiverEmail){
                friend.unread = 0;
                rankOnlineUsers();
            }
        })
        // New - END
    }

    // New - Unread: unread notification
    const receiveUnread = (data) =>{ 
        friends.forEach(friend => { //每次收到一条未读信息就会被trigger，因此data里只有一个senderEmail
            if (friend.email == data.senderEmail){
                friend.unread += 1;
                // 如果有其他收到未读信息用户的UI方面的更新，加在这里
                rankOnlineUsers();
            }
        })
    }
    // New - END


    // New - Unread: update last chat friend for this user function
    const updateLastChatFriend = async (lastChatFriendEmail) =>{
        const message_body = JSON.stringify({
            userEmail,  
            receiverEmail:lastChatFriendEmail, // new receiver email
        });

        await fetch(base_url+'/api/chat/lastchat/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: message_body
        });
    }
    // New - END

    // Chat implementation - switch the chatting user by click friend avatar
    const switchToChat = async (friend) => {
        console.log("switchToChat triggered", friend.email);
        receiverEmail = friend.email;  // Update the receiverEmail
        switchReceiver();  // Switch to the new receiverEmail
    }

    // Chat implementation - 整个函数模拟用户重新登陆的过程测试好友列表用，implementation时用不到
    const switchMainUser = async () => {
        mainUserInfo = {email: userEmail, avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/1.webp', name: 'Main User'}
        
        friends = [];
        friendChannel.unbind(prevFriendChannelName);

        unsubscribeOnlineChannel();

        // New - 这个整个大函数模拟用户重新登陆的过程测试好友列表用，implementation时用不到
        // New - need to update the pusher setup method
         pusher = new Pusher(config.key, {
            cluster: config.cluster,
            authEndpoint: base_url + "/api/chat/auth/",
            auth: {
                params: { email: userEmail },  // 无需 JSON.stringify，直接发送对象即可
            },
        });
        friendChannel = pusher.subscribe(mainUserInfo["email"]);
        friendChannel.bind('newfriend', data => receiveNewFriend(data));

        fetchFriendList();
        prevFriendChannelName = mainUserInfo["email"];

    }

    // Chat implementation - Format (Unix Time * 1000) to readable format 
    function formatUnixTime(unixTime) {
        const milliseconds = unixTime;

        const date = new Date(milliseconds);

        const year = date.getFullYear().toString().slice(-2);
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hour = String(date.getHours() % 12 || 12);
        const minute = String(date.getMinutes()).padStart(2, '0');
        const ampm = date.getHours() >= 12 ? 'pm' : 'am';

        const formattedTime = `${year}-${month}-${day} ${hour}:${minute} ${ampm}`;

        return formattedTime;
    }


    //for debug
    const printMessages = () => {
     submit();
     console.log(messages);
    }


</script>
<div class="container">

    <!-- Friend List UI Implementation -->
    <div class="friend-list">
        <h2>Main User</h2>
        <div class="friend">
            <img src={mainUserInfo.avatar} alt={mainUserInfo.name} class="friend-avatar" />
            <div class="friend-info">
                <div class="friend-name">{mainUserInfo.name}</div>
                <div class="friend-email">{mainUserInfo.email}</div>
            </div>
        </div>
        <h2>Friend List</h2>
        <div class="friends">
            {#each friends as friend}
                <div class="friend" on:click={() => switchToChat(friend)}>
                    <img src={friend.avatar} alt={friend.name} class="friend-avatar" />
                    <div class="friend-info">
                        <div class="friend-name">{friend.name}</div>
                        <div class="friend-email">{friend.email}</div>
                        <div class="friend-email">unread: {friend.unread}</div>
                        <div class="friend-email">{friend.status}</div>
                    </div>
                </div>
            {/each}
        </div>
    </div>


        <!-- Chat Window UI Implementation -->
    <div class="d-flex flex-column align-items-stretch flex-shrink-0 bg-white">
        <div class="d-flex align-items-center flex-shrink-0 p-3 link-dark text-decoration-none border-bottom">
            <input class="fs-5 fw-semibold" placeholder="Main user email" bind:value={userEmail}/>
            <button type="button" on:click={switchMainUser}>Login</button> 

        </div>
        <div class="list-group list-group-flush border-bottom scrollarea">
            {#each messages as msg}
                <div class="list-group-item list-group-item-action py-3 lh-tight">
                    <div class="d-flex w-100 align-items-center justify-content-between">
                        <strong class="mb-1">{msg.userEmail}</strong>
                    </div>
                    <div class="col-10 mb-1  small">{msg.message} <span style="color: gray; font-style: italic;">{formatUnixTime(msg.timestamp)}</span></div>
                </div>

            {/each}
        </div>
    </div>
    <form on:submit|preventDefault={submit}>
        <input class="form-control" placeholder="Write a message" bind:value={message}/>
        <button type="button" on:click={printMessages}>Send Message</button> 
    </form>
    <input class="form-control" placeholder="Switch receiverEmail" bind:value={receiverEmail}/>
    <button type="button" on:click={switchReceiver}>Switch to new receiverEmail</button> 
    <input class="form-control" placeholder="New friend email" bind:value={newFriendEmail}/>
    <button type="button" on:click={addNewFriend}>Add New Friend</button> 
</div>

<style>
    .scrollarea {
        min-height: 500px;
    }

    /* Friend List Style */
    .friend-list {
        width: 200px; 
        padding: 10px;
        border-right: 1px solid #ddd; 

    }
    .friend {
        display: flex;
        align-items: center;
        cursor: pointer;
        padding: 5px;
        
    }
    .friend-avatar {
        width: 30px; 
        height: 30px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .friend-info .friend-name {
        font-weight: bold;
    }
    .friend-info .friend-email {
        color: #555;
    }
    
</style>
