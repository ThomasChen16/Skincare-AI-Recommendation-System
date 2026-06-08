from skincareAI import have_conversation
from embedding_model import load_model

def main():
    load_model()
    have_conversation()
    
if __name__ == "__main__":
    main()