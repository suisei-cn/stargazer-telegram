# Stargazer Telegram

![Publish Docker](https://github.com/suisei-cn/stargazer-telegram/workflows/Publish%20Docker/badge.svg)

Stargazer Telegram is the telegram frontend for [PyStargazer](https://github.com/suisei-cn/stargazer-subscriber)
and Stargazer Subscriber Backend.

It's one of all the stargazer bots, which allow users of different instant messaging apps
to keep track of vtubers they like and support.

Telegram: [@pystargazer_bot](https://t.me/pystargazer_bot)

## Related Projects

[PyStargazer](https://github.com/suisei-cn/pystargazer) - PyStargazer is a flexible vtuber tracker. It's now capable of monitoring Youtube live status, new tweets, and bilibili dynamic.

[Stargazer Subscriber](https://github.com/suisei-cn/stargazer-subscriber) - Stargazer Subscriber is the universal frontend of stargazer bots.

`Stargazer Subscriber Backend` - The python backend of stargazer subscriber.

`StargazerQQ` - UserID: 2733773638

## Deploy

1. Make sure that [PyStargazer](https://github.com/suisei-cn/pystargazer) is running and its websocket path is accessible.
2. Bring up `Stargazer Subscriber Backend` and note down the M2M token.
3. Start serving [Stargazer Subscriber](https://github.com/suisei-cn/stargazer-subscriber).
4. Set the environment variables (`M2M_TOKEN`, `BACKEND_URL`, `FRONTEND_URL`, `MESSAGE_WS`) accordingly and
start the container.

## License

This project is licensed under MIT License - see the [LICENSE.md](LICENSE.md) file for details.
