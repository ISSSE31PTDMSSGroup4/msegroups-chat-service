<script>
    import {onMount} from 'svelte';
    import Pusher from 'pusher-js';

    let pusher;
    let channel;
    let prevChannelName;

    let userEmail = 'username@gmail.com';
    let receiverEmail = "";
    let message = '';

    //mock user info for test
    let name = 'Jack';  // User's name, should be initialized based on your app's user data
    let avatar =  "https://mdbcdn.b-cdn.net/img/new/avatars/2.webp";  // User's avatar URL, should be initialized based on your app's user data
    let userId = 1;  // should be initialized based on your app's user data

    let messages = [];
    let base_url = "http://localhost:8000";

    let newFriendEmail = "";

    
    // Chat Implementation - 模拟从profile那边拿到的main user信息
    let mainUserInfo = {email: userEmail, 
                        avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/1.webp', 
                        name: 'Main User',
                        userID: 1
                    };

    // 模拟的朋友列表数据
    let friends = [

    ];


    // Chat Implementation - Setup Pusher when the component is mounted
    onMount(async () => {
        Pusher.logToConsole = true;

        // Fetch Pusher configuration from the backend
        const response = await fetch(base_url+'/api/chat/config');
        const config = await response.json();

        pusher = new Pusher(config.key, // pusher key
        {
            cluster: config.cluster,
        });
    })

    // Chat implementation - Send Message
    const submit = async () => {
        console.log("submit triggered");

        const channelName = prevChannelName;

        const message_body = JSON.stringify({
            channelName,  // assuming this is determined somewhere in your chat logic
            user: {
                userId,  // this could be the user's ID from your system
                name,  // the user's name from your system
                avatar,  // the user's avatar URL
            },
            message,  // the message text
            userEmail,  // the email of the user sending the message
            receiverEmail,  // the email of the message recipient
        });

        await fetch(base_url+'/api/chat/message', {
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
        
        console.log(channelName);

        return channelName;
    }

    // Chat implementation - Get chat history
    const fetchHistory = async () => {
        const response = await fetch(base_url + '/api/chat/history',{
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

    // Chat implementation - UI messages update helper
    const receiveNewMessage = (data) =>{
        messages = [...messages, data];
    }

    // Chat implementation - Swicth the chatting user
    const switchReceiver = async () => {
        console.log("userEmail: " + receiverEmail);
        
        let newChannelName = getChannelName(userEmail, receiverEmail);

        if (channel) {
            channel.unbind('message'); 
            pusher.unsubscribe(prevChannelName); 
        }

        channel = pusher.subscribe(newChannelName);
        
        prevChannelName = newChannelName

        // Fetch chat history when switching receiver
        fetchHistory();

        messages = [];
        channel.bind('message', data => receiveNewMessage(data));

    }

    const switchMainUser = async () => {
        mainUserInfo = {email: userEmail, avatar: 'https://mdbcdn.b-cdn.net/img/new/avatars/1.webp', name: 'Main User'}
    }

    // Chat implementation - Time
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



    function switchToChat(friend) {
        console.log("switchToChat triggered", friend.email);
        // receiverEmail = friend.email;  // 设置接收者的邮箱
        // switchReceiver();  // 切换聊天对象
    }

    //for debug
    const printMessages = () => {
     submit();
     console.log(messages);
    }


</script>
<div class="container">

    <!-- Friend List Implementation -->
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
                    </div>
                </div>
            {/each}
        </div>
    </div>


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
                    <div class="col-10 mb-1 small">{msg.message} <span style="color: gray; font-style: italic;">{formatUnixTime(msg.timestamp)}</span></div>
                </div>

            {/each}
        </div>
    </div>
    <form on:submit|preventDefault={submit}>
        <input class="form-control" placeholder="Write a message" bind:value={message}/>
        <button type="button" on:click={printMessages}>Send Message</button> 
    </form>
    <input class="form-control" placeholder="Switch userEmail" bind:value={receiverEmail}/>
    <button type="button" on:click={switchReceiver}>Switch to new userEmail</button> 
    <input class="form-control" placeholder="New friend email" bind:value={newFriendEmail}/>
    <button type="button" on:click={printMessages}>Add New Friend</button> 
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
