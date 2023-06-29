"""
Simple model cache that loads models from disk and caches them in memory. with a least recently used eviction policy.
"""
import logging
from collections import OrderedDict
from typing import Callable
import os
import gc

import torch.cuda
from loguru import logger

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ModelCache:
    """
    can only hold one model at a time right now
    loads models in and out of disk/gpu memory
    """

    def __init__(self, max_size_gb: int = 24):
        self.max_size_gb = max_size_gb
        self.cache = OrderedDict()
        self.most_recent_name = None
        # self.loaded_models = set()

    def __len__(self):
        return len(self.cache)

    # def is_loaded(self, model_name: str) -> bool:
    #     return model_name in self.loaded_models

    def add_or_get(self, model_name: str, add_model_func: Callable):
        self.most_recent_name = model_name
        if len(self.cache) > 0:
            # evict all models not in use
            for evicted_model_name, evicted_model in self.cache.items():
                if evicted_model_name == model_name:
                    # dont evict this current model
                    continue
                logging.info(f"Evicting model {evicted_model_name} from cache")
                # iterate if is iterable
                try:
                    if type(evicted_model) == list or type(evicted_model) == tuple:
                        for model in evicted_model:
                            model.to("cpu") # todo try each model to sometimes can fail/dont rely o
                            # if model_name == "chat":
                            #     del model

                except Exception as e:
                    # logging.info(e) # is probably fine
                    pass
                try:
                    evicted_model.to("cpu")
                    # if model_name == "chat":
                    #     del evicted_model
                except Exception as e:
                    pass

                # chat_model needs hard eviction/reloading for some reason???
                # this is annoying/slow to switch this model out
                # if "chat" in evicted_model_name:
                #     logging.info(f"hard evicting model {evicted_model_name}")
                #     del evicted_model
                #     del self.cache[evicted_model_name]


                #breaks things
                # from numba import cuda
                # device = cuda.get_current_device()
                # device.reset()

                # todo need this to save mem?
                try:
                    gc.collect()
                    torch.cuda.empty_cache()
                except Exception as e:
                    logger.info("restarting to fix cuda issues")
                    os.system("/usr/bin/bash kill -SIGHUP `pgrep gunicorn`")
                    os.system("kill -1 `pgrep gunicorn`")

                logging.info(f"Evicted model {evicted_model_name} from cache")

        if model_name in self.cache:
            logging.info(f"ensuring model {model_name} on gpu")
            try:
                for model in self.cache[model_name]:
                    # todo this assumes ordering - the processor woudl fail to be moved to gpu note
                    current_device = next(model.parameters()).device
                    if current_device != DEVICE:
                        model.to(DEVICE)
                        logging.info(f"switched model {model_name} to gpu")
                        self.cache[model_name] = add_model_func() # should load idempotently/be used to reload custom model if needed?
                        break
            except Exception as e:
                logger.error(e)
                # logging.info(e) # is probably fine
                pass
            try:
                current_device = next(self.cache[model_name].parameters()).device
                if current_device != DEVICE:
                    # todo why are we being so defensive? should be fast to move to the gpu twice/not the worst thing
                    # but if we forget to move to the gpu its a big deal/crashes

                    # self.cache[model_name].to(DEVICE)
                    self.cache[model_name] = add_model_func() # should load idempotently/be used to reload custom model if needed?
            except Exception as e:
                pass
            logging.info(f"ensured model {model_name} on gpu")

            return self.cache[model_name]

        self.cache[model_name] = add_model_func()
        # self.loaded_models.add(model_name)
        logging.info(f"Added model {model_name} to cache")
        return self.cache[model_name]

    def get(self, model_name: str) -> Callable:
        if model_name not in self.cache:
            raise RuntimeError(f"Model {model_name} not found in cache")
        return self.cache[model_name]

    def empty_all_caches(self):
        for evicted_model_name, evicted_model in self.cache.items():
            # remove any model thats on the cpu to save memory
            # iterate if is iterable
            try:
                for model in evicted_model:
                    model.to("cpu")
                    del model

            except Exception as e:
                # logging.info(e) # is probably fine
                pass
            try:
                evicted_model.to("cpu")
            except Exception as e:
                pass

            # chat_model needs hard eviction/reloading for some reason???
            # this is annoying/slow to switch this model out
            del evicted_model
            del self.cache[evicted_model_name]
            try:
                torch.cuda.empty_cache()
            except Exception as e:
                logger.error("cuda error")
                logger.error(e)
                # logger.info("restarting to fix cuda issues")
                # os.system("/usr/bin/bash kill -SIGHUP `pgrep gunicorn`")
                # os.system("kill -1 `pgrep gunicorn`")
    def unload_all_but_current_model_save_mem(self):
        models_to_evict = []
        for evicted_model_name, evicted_model in self.cache.items():

            logging.info(f"Evicting model {evicted_model_name} from cache")
            # iterate if is iterable
            try:
                for model in evicted_model:
                    current_device = next(model.parameters()).device
                    if current_device != DEVICE:
                        del model
                        models_to_evict.append(evicted_model_name)
            except Exception as e:
                logging.info(e) # is probably fine
                pass
            try:
                current_device = next(evicted_model.parameters()).device
                if current_device != DEVICE:
                    del evicted_model
                    models_to_evict.append(evicted_model_name)

            except Exception as e:
                pass

            # chat_model needs hard eviction/reloading for some reason???
            # this is annoying/slow to switch this model out
            # try:
            #     torch.cuda.empty_cache()
            # except Exception as e:
            #     logger.error("cuda error")
            #     logger.error(e)
                # logger.info("restarting to fix cuda issues")
                # os.system("/usr/bin/bash kill -SIGHUP `pgrep gunicorn`")
                # os.system("kill -1 `pgrep gunicorn`")
        for model_name in models_to_evict:
            del self.cache[model_name]
