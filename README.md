# github
A GitHub client and webhook receiver for maubot.

## Basic setup
1. Set up the plugin like any other maubot plugin.
2. Register a GitHub OAuth application to get a `client_id` and `client_secret`.
   Set the callback URL to `https://{maubot_host}/{plugin_base_path}/{instance_id}/auth`.
3. Use `!github login` to log in.
4. Use `!github webhook add <owner>/<repo>` to add webhooks.
