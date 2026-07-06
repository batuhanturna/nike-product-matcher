from sentence_transformers import SentenceTransformer, util


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print("Compare Two Product Texts")

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    text1 = input("\nEnter first product text: ").strip()
    text2 = input("Enter second product text: ").strip()

    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)

    score = util.cos_sim(embedding1, embedding2)[0][0].item()

    print("\nSimilarity score:")
    print(f"{score:.4f}")

    if score >= 0.80:
        print("Result: Very similar")
    elif score >= 0.60:
        print("Result: Similar")
    elif score >= 0.40:
        print("Result: Medium similarity")
    else:
        print("Result: Weak similarity")


if __name__ == "__main__":
    main()
