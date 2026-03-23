from src.model_provider import ModelProvider

provider = ModelProvider()
model = provider.get_model(model_name="ollama", config_manager=None)

print(model)


print(model.test_connection())
print("tested successfully")