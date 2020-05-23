# github
A GitHub client and webhook receiver for maubot.

## Hosted instance
You can use the instance hosted on maunium.net by talking to
[@github:maunium.net](https://matrix.to/#/@github:maunium.net).

See steps 4 and 5 below.

## Basic setup
1. **Set up the plugin like any other maubot plugin.**

   You just have to upload the plugin, and then create an instance i.e. an association of a plugin and a client. 
   
   You have to give this new instance an `instance_id` / a name, for example "my_github_bot"

2. **[Register a GitHub OAuth application](https://github.com/settings/developers) to get a `client_id` and `client_secret`.**

   Set the callback URL to `https://{maubot_host}/{plugin_base_path}/{instance_id}/auth` 

   Following our example, if your instance is hosted on `maubot.example.com` and you kept the default `plugin_base_path` i.e. `_matrix/maubot/plugin`, the Github's new oAuth App's form should go like this:

   * Application name: My Github Bot
   * Homepage URL: https://maubot.example.com/
   * Application description: A Maubot Github bot for tracking repositories! Yay!
   * Authorization callback URL: https://maubot.example.com/_matrix/maubot/plugin/my_github_bot/auth

3. **Set the `client_id` and `client_secret` in maubot.**

   Copy these informations from your Github's oAuth App page and paste them in the instance page options.
   ```
   client_id: <replace>
   client_secret: <replace>
   ```
   
   And save the instance configuration.

4. **Use `!github login` to log in.**

   After inviting your bot / client to a matrix channel, use the `!gh` or `!github` command to use the github instance.
   
   Using `gh login` first is mandatory and needed once **per instance**.
   
   The bot will reply with a link leading to your personal Github's allowed oAuth apps page, where you shall grant the necessary rights to the bot oAuth app.

5. **Use `!github webhook add <owner>/<repo>` to add webhooks.**

   This will let you see in the current channel all the commits, comments, issues, stars, forks, pull requests, and so on, for that given repository.
   
   You must have admin rights on the repositories you want to track, as adding webhooks to a repository requires manager access rights to a project.

   Once you create a webhook and track a repository, it will be tracked **only in the room from which you are in**.
