# Moss desktop app
An app for working with your documents in the reMarkable cloud

This project is entirely open source.
If you encounter any issues, you can use the github issues to let the contributors know! 

## Installation & Portable mode
You'll find builds under releases

The executable contains the app and an installer.
You can choose to skip install and run the app that way.
If you install it'll add to path for linux `moss`.
or for windows it'll also add desktop and start menu options.

If the installer fails to launch the app or install it, please open an issue.

## Usage notes
Using this app to access your reMarkable cloud
may cause reMarkable to take action on your account.
So use this app at your own discretion! 

The app supports the api completely!

For information on how you can use moss
check out the [wiki](https://github.com/JustRedTTG/moss-desktop/wiki)!

## Contribution
This section describes the steps for contributors to best setup their work environment

**Your feature must be compatible with python 3.9**

1. Run the moss.py file
2. In the app input your cloud code
3. Wait for the initial sync
4. Please note that if you are developing changes to the cache system, all cached files are stored in sync folder
5. Make changes and test a new feature
The look and feel of this feature has to be paper-like
- Use the config.json, you can set `debug` to `true` in there! 
6. Make your pull request.
A few things will be checked
- Different screen resolution support
- API compatibility
- etc.

## Extensions
***Coming soon...***

Here are some planned extensions I will create!
The system will be open for people to make extensions on their own
- Replace PDF function (the origin of this whole project)
- PDF Templates Store (with update support)
- nyaa.si ebook/pdf download
- Image(s) to PDF import
- Add Image to PDF function (from suggestion)
- Extension Store (A hub of verified extensions)