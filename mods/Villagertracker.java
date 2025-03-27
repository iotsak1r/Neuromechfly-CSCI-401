package com.example.villagertracker;

import com.google.gson.Gson;
import net.minecraft.entity.merchant.villager.VillagerEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.world.World;
import net.minecraft.world.server.ServerWorld;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.server.ServerLifecycleHooks;
import net.minecraft.entity.player.ServerPlayerEntity;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Mod("villagertracker")
public class Villagertracker {
    private static final String OUTPUT_FILE = "villager_positions.json";

    public Villagertracker() {
        MinecraftForge.EVENT_BUS.register(this);
    }

    @SubscribeEvent
    public void setup(final FMLCommonSetupEvent event) {
    }

    @SubscribeEvent
    public void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase == TickEvent.Phase.END) {
            MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
            if (server != null) {
                ServerWorld world = server.getLevel(World.OVERWORLD);
                if (world != null) {
                    if (!server.getPlayerList().getPlayers().isEmpty()) {
                        ServerPlayerEntity player = server.getPlayerList().getPlayers().get(0);

                        double range = 50;
                        AxisAlignedBB aabb = new AxisAlignedBB(
                                player.getX() - range, player.getY() - range, player.getZ() - range,
                                player.getX() + range, player.getY() + range, player.getZ() + range
                        );
                        // Find VillagerEntities
                        List<VillagerEntity> villagers = world.getEntitiesOfClass(
                                VillagerEntity.class,
                                aabb,
                                villager -> true
                        );
                        System.out.println("Found " + villagers.size() + " villagers near the player");

                        List<VillagerInfo> villagerInfos = new ArrayList<>();
                        for (VillagerEntity villager : villagers) {
                            villagerInfos.add(new VillagerInfo(
                                    villager.getName().getString(),
                                    villager.getX(),
                                    villager.getY(),
                                    villager.getZ()
                            ));
                        }
                        writeVillagerPositions(villagerInfos);
                    } else {
                        System.out.println("No players found");
                    }
                }
            }
        }
    }


    private void writeVillagerPositions(List<VillagerInfo> villagerInfos) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(villagerInfos);
        try (FileWriter writer = new FileWriter(OUTPUT_FILE)) {
            writer.write(json);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static class VillagerInfo {
        public String name;
        public double x;
        public double y;
        public double z;

        public VillagerInfo(String name, double x, double y, double z) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}