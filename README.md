# prompt-injection-langGraph-  
  

## setup:

    
### Setup ENV
    export OPENAI_API_KEY=openapi_token
    export REST_API_KEY=rest_api_key
    export REST_API_ROOT_URL=root_url
	

### Create Virtual Env
	
	python3 -m venv venv
    pip3 install -r requirements.txt


### Setup MyAssistantApp
		
	cd MyAssistantApp
	fastapi run

	Expose the application to the public internet by port forwarding, 		 Cloudflare Tunnel, Ngrok


### Setup Root application

	From the root project folder 
	python3 main.py
	  

	
		