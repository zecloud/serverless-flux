import azure.functions as func
import logging
from io import BytesIO
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel, CLIPTextModel
from optimum.quanto import freeze, qfloat8, quantize



app = func.FunctionApp()

@app.queue_trigger(arg_name="azqueue", queue_name="flux",
                               connection="fluxstorage") 
@app.blob_output(arg_name="outputblob",
                path="fluximages/{rand-guid}.png",
                datatype="binary",
                connection="fluxstorage")
def flux(azqueue: func.QueueMessage,outputblob: func.Out[func.InputStream]):
    logging.info('Python Queue trigger processed a message: %s',
                azqueue.get_body().decode('utf-8'))
    bfl_repo = "black-forest-labs/FLUX.1-dev"
    dtype = torch.bfloat16

    transformer = FluxTransformer2DModel.from_single_file("https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors", torch_dtype=dtype)
    quantize(transformer, weights=qfloat8)
    freeze(transformer)

    text_encoder_2 = T5EncoderModel.from_pretrained(bfl_repo, subfolder="text_encoder_2", torch_dtype=dtype)
    quantize(text_encoder_2, weights=qfloat8)
    freeze(text_encoder_2)

    pipe = FluxPipeline.from_pretrained(bfl_repo, transformer=None, text_encoder_2=None, torch_dtype=dtype)
    pipe.transformer = transformer
    pipe.text_encoder_2 = text_encoder_2

    pipe.enable_model_cpu_offload()

    prompt = azqueue.get_body().decode('utf-8')
    image = pipe(
        prompt,
        guidance_scale=3.5,
        output_type="pil",
        num_inference_steps=20,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]
    bIO = BytesIO()
    image.save(bIO, format="png")
    outputblob.set(bIO.getvalue())

    
