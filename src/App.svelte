<script>
    import {onMount} from 'svelte';
    import Pusher from 'pusher-js';

    let pusher;
    let channel;

    let username = 'username';
    let receiver = "";
    let message = '';
    let messages = [];
    let new_messages = [
        {
		'username' : "user for test",
		'message' : "hello"
        }
    ];

    onMount(async () => {
        Pusher.logToConsole = true;

        // Fetch Pusher configuration from the backend
        const response = await fetch('http://localhost:8000/api/pusher_config');
        const config = await response.json();

        pusher = new Pusher(config.key, 
        // pusher key
        {
            cluster: config.cluster,
            // authEndpoint: '/pusher/auth'
        });
    })

    const submit = async () => {
        console.log("submit triggered");

        let date = new Date();
        let localTime = date.toLocaleString('en-US', { timeZone: 'Asia/Singapore' });

        await fetch('http://localhost:8000/api/messages', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username,
                receiver,
                message,
                time: localTime
            })
        });

        message = '';
    }

    function getChannelName(username,receiver){
        // Sort the usernames
        const sortedUsernames = [username, receiver].sort();

        // Join with a delimiter
        const channelName = sortedUsernames[0] + "-" + sortedUsernames[1];
        
        console.log(channelName);

        return channelName;
    }

    const fetchHistory = async () => {
        const response = await fetch('http://localhost:8000/api/history',{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username,
                receiver,
            })
        });
        const data = await response.json();
        if (data && data.length > 0) {
                messages = data;
            } 
        console.log("history result: ", messages);
    }

    const switchReceiver = () => {
        console.log("receiver: " + receiver);

        channel = pusher.subscribe(getChannelName(username, receiver));
        
        // Fetch chat history when switching receiver
        fetchHistory();

        messages = [];
        channel.bind('message', data => {
            messages = [...messages, data];
        });
        // messages = new_messages
    }

    const printMessages = () => {
     submit();
     console.log(messages);   
    }


</script>

<div class="container">
    <div class="d-flex flex-column align-items-stretch flex-shrink-0 bg-white">
        <div class="d-flex align-items-center flex-shrink-0 p-3 link-dark text-decoration-none border-bottom">
            <input class="fs-5 fw-semibold" bind:value={username}/>
        </div>
        <div class="list-group list-group-flush border-bottom scrollarea">
            {#each messages as msg}
                <div class="list-group-item list-group-item-action py-3 lh-tight">
                    <div class="d-flex w-100 align-items-center justify-content-between">
                        <strong class="mb-1">{msg.username}</strong>
                    </div>
                    <div class="col-10 mb-1 small">{msg.message} <span style="color: gray; font-style: italic;">{msg.time}</span></div>
                </div>
            {/each}
        </div>
    </div>
    <form on:submit|preventDefault={submit}>
        <input class="form-control" placeholder="Write a message" bind:value={message}/>
        <button type="button" on:click={printMessages}>Send Message</button> 

    </form>
    <input class="form-control" placeholder="Switch receiver" bind:value={receiver}/>
    <button type="button" on:click={switchReceiver}>Switch to new receiver</button> 
</div>

<style>
    .scrollarea {
        min-height: 500px;
    }
</style>
