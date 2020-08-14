using System.Collections.Generic;
using UnityEngine;

public class DifficultyCalculator
{
    public string songID;

    public CalculatedDifficulty expert;
    public CalculatedDifficulty advanced;
    public CalculatedDifficulty standard;
    public CalculatedDifficulty beginner;

    public DifficultyCalculator(SongList.SongData songData)
    {
        this.songID = songData.songID;
        EvaluateDifficulties(songData);
    }

    private void EvaluateDifficulties(SongList.SongData songData)
    {
        if (songData.hasExpert)
            this.expert.EvaluateCues(SongCues.GetCues(songData, KataConfig.Difficulty.Expert), songData);
        if (songData.hasHard)
            this.expert.EvaluateCues(SongCues.GetCues(songData, KataConfig.Difficulty.Hard), songData);
        if (songData.hasNormal)
            this.expert.EvaluateCues(SongCues.GetCues(songData, KataConfig.Difficulty.Normal), songData);
        if (songData.hasEasy)
            this.expert.EvaluateCues(SongCues.GetCues(songData, KataConfig.Difficulty.Easy), songData);
    }
}
public class CalculatedDifficulty
{
    public static float spacingMultiplier = 0.25f;
    public static float lengthMultiplier = 1f;
    public static float densityMultiplier = 1f;

    public float difficultyRating;
    public float spacing;
    public float density;
    public float readability;

    float length;

    public static Dictionary<Target.TargetBehavior, float> objectDifficultyModifier = new Dictionary<Target.TargetBehavior, float>()
    {
        { Target.TargetBehavior.Standard, 1f },
        { Target.TargetBehavior.Vertical, 1.2f },
        { Target.TargetBehavior.Horizontal, 1.3f },
        { Target.TargetBehavior.Hold, 1f },
        { Target.TargetBehavior.ChainStart, 1.2f },
        { Target.TargetBehavior.Chain, 0.2f },
        { Target.TargetBehavior.Melee, 0.6f }
    };

    List<SongCues.Cue> leftHandCues = new List<SongCues.Cue>();
    List<SongCues.Cue> rightHandCues = new List<SongCues.Cue>();
    List<SongCues.Cue> eitherHandCues = new List<SongCues.Cue>();
    List<SongCues.Cue> allCues = new List<SongCues.Cue>();

    public void EvaluateCues(SongCues.Cue[] cues, SongList.SongData songData)
    {
        this.length = AudioDriver.TickSpanToMs(songData, cues[0].tick, cues[cues.Length - 1].tick);
        SplitCues(cues);
        CalculateSpacing();
        CalculateDensity();
        CalculateReadability();
        difficultyRating = spacing + readability;
    }

    void CalculateReadability()
    {
        for (int i = 0; i < allCues.Count; i++)
        {
            float modifierValue = 0f;
            objectDifficultyModifier.TryGetValue(allCues[i].behavior, out modifierValue);
            readability += modifierValue;
        }
        readability /= length;
    }

    void CalculateSpacing()
    {
        GetSpacingPerHand(leftHandCues);
        GetSpacingPerHand(rightHandCues);
        spacing /= length;
    }

    void CalculateDensity()
    {
        density = (float) allCues.Count / length;
    }

    private void GetSpacingPerHand(List<SongCues.Cue> cues)
    {
        for (int i = 1; i < cues.Count; i++)
        {
            float dist = Vector2.Distance(GetTrueCoordinates(cues[i]), GetTrueCoordinates(cues[i - 1]));
            float distMultiplied = cues[i].behavior == Target.TargetBehavior.Melee ? float.Epsilon :
                dist * spacingMultiplier;
            spacing += distMultiplied;
        }
    }

    Vector2 GetTrueCoordinates(SongCues.Cue cue)
    {
        float x = cue.pitch % 12;
        float y = (int)(cue.pitch / 12);
        x += cue.gridOffset.x;
        y += cue.gridOffset.y;
        return new Vector2(x, y);
    }

    void SplitCues(SongCues.Cue[] cues)
    {
        for (int i = 0; i < cues.Length; i++)
        {
            allCues.Add(cues[i]);
            switch (cues[i].handType)
            {
                case Target.TargetHandType.Left:
                    leftHandCues.Add(cues[i]);
                    break;
                case Target.TargetHandType.Right:
                    rightHandCues.Add(cues[i]);
                    break;
                case Target.TargetHandType.Either:
                    eitherHandCues.Add(cues[i]);
                    break;
                default:
                    break;
            }
        }
    }
}