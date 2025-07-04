# Application Cog Documentation

## Overview

The `Application` cog allows server administrators to set up application processes for specific roles. Users can apply for roles by answering custom questions via DM, and admins can review applications.

## Commands

### 1. `[p]appset add <role_mention> <question>`
- **Description**: Add a question for a specific role to the application process.
- **Permissions**: Manage Server
- **Example**: `[p]appset add @Moderator What experience do you have moderating Discord servers?`

### 2. `[p]appset set <channel_mention>`
- **Description**: Set the application channel where applications will be sent.
- **Permissions**: Manage Server
- **Example**: `[p]appset set #applications`

### 3. `[p]appset listroles`
- **Description**: List roles available for application in this server.
- **Permissions**: Manage Server
- **Example**: `[p]appset listroles`

### 4. `[p]apply <role_name>`
- **Description**: Apply for a specific role by answering configured questions via DM.
- **Permissions**: None
- **Example**: `[p]apply Moderator`

### 5. `[p]appset review <role_name> <member_mention>`
- **Description**: Review a member's application for a specific role.
- **Permissions**: Manage Server
- **Example**: `[p]appset review Moderator @user`

### 6. `[p]appset removeq <role_mention> <question>`
- **Description**: Remove a question for a specific role.
- **Permissions**: Manage Server
- **Example**: `[p]appset removeq @Moderator What experience do you have moderating Discord servers?`

### 7. `[p]appset clearq <role_mention>`
- **Description**: Clear all questions for a specific role.
- **Permissions**: Manage Server
- **Example**: `[p]appset clearq @Moderator`

## Notes
- Only users with Manage Server permissions can configure application questions and channels.
- Users apply for roles via DM and their responses are sent to the configured application channel.