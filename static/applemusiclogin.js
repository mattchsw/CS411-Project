document.cookie = "username=AwadCookie; SameSite=Lax; Secure";
document.addEventListener('musickitloaded', async function() {
    // here configuration of MusicKit Instance and all the playback
    try {
        await MusicKit.configure({
            developerToken: "{{ developer_token }}",
            app: {
                name: 'Playlist Transfer App',
                build: '1.0',
            },
        });
    } catch(error) {
         console.error("Authorization failed", error);
    }
    const music = MusicKit.getInstance();
    await music.authorize();
});

