<h1 align="center">🍪 Examples & Recipes</h1>

<h3 align="center">Customize your EvoQuant — harness it, make it yours.</h3>

| Example                                                     | Description                                                                     |
|------------------------------------------------------------|---------------------------------------------------------------------------------|
| [Survey literature](https://github.com/CamusGIT/EvoQuant/tree/main/docs/examples/survey-literature#literature-survey)   | Run EvoQuant with the `paper-navigator` skill to produce a bilingual, conference-grade literature survey |


| Recipe                                                     | Description                                                                     |
|------------------------------------------------------------|---------------------------------------------------------------------------------|
| [macOS 24/7 Deployment](https://github.com/CamusGIT/EvoQuant/blob/main/docs/recipes/deployment-macos-24h.md#running-evoquant-247-on-macos-telegram-bot--stt--ccproxy)   | Run EvoQuant as an always-on service on macOS with OAuth + Telegram + STT   |

## Contributing a Recipe

See the [Contributing Guide](../CONTRIBUTING.md) for general guidelines. When adding a new recipe:

- **Use `EvoQuant` CLI** — recipes should work with `EvoQuant serve`, `EvoQuant config`, or `EvoQuant onboard`
- **Pin dependencies** — specify EvoQuant extras (e.g., `pip install -e ".[telegram,stt]"`)
- **Include a README** with clear setup and usage instructions
- **Keep it focused** — each recipe should demonstrate one deployment or integration scenario
- **Add to the table** above so others can discover it
