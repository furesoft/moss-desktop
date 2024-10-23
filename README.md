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
In order to run the app with all the features
you have to use **python 3.9** due to `cefpython`
This will allow for the usage of the following features:
- PDF support with links
- perhaps more features in the future

Using this app to access your reMarkable cloud
may cause reMarkable to take action on your account.
So use this app at your own discretion! 

The app supports the old API, 
hanse some if not all features should work with
any third-party self-hosted clouds that implement the old API
Please also note that there's a chance newer reMarkable
versions to remove support for the old API, so your usage maybe be limited, 
unless someone develops a third-party cloud capable of supporting both the new and old APIs, 
but since this app supports the new API it should work in most cases

## Contribution
This section describes the steps for contributors to best setup their work environment

**Install python 3.9 if you want to use cef for a feature!**

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